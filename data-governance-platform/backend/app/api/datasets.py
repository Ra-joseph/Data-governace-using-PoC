from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.dataset import Dataset
from app.schemas.dataset import (
    DatasetCreate, DatasetUpdate, DatasetResponse,
    SchemaImportRequest, SchemaImportResponse, TableInfo,
    DatasetStatus
)
from app.services.contract_service import ContractService
from app.services.postgres_connector import PostgresConnector
from app.config import settings

router = APIRouter(prefix="/datasets", tags=["datasets"])
contract_service = ContractService()


@router.post("/", response_model=DatasetResponse, status_code=201)
def create_dataset(dataset: DatasetCreate, db: Session = Depends(get_db)):
    """
    Create a new dataset with automatic contract generation and validation.
    """
    # Check if dataset with same name exists
    existing = db.query(Dataset).filter(Dataset.name == dataset.name).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Dataset with name '{dataset.name}' already exists")
    
    # Detect if dataset contains PII
    contains_pii = any(field.pii for field in dataset.schema_definition)
    
    # Create dataset record
    db_dataset = Dataset(
        name=dataset.name,
        description=dataset.description,
        owner_name=dataset.owner_name,
        owner_email=dataset.owner_email,
        source_type=dataset.source_type.value,
        source_connection=dataset.source_connection,
        physical_location=dataset.physical_location,
        schema_definition=[field.dict() for field in dataset.schema_definition],
        classification=dataset.governance.classification.value,
        contains_pii=contains_pii,
        compliance_tags=dataset.governance.compliance_tags,
        status=DatasetStatus.DRAFT.value
    )
    
    db.add(db_dataset)
    db.commit()
    db.refresh(db_dataset)
    
    # Create initial contract
    try:
        contract = contract_service.create_contract_from_dataset(db, db_dataset.id, version="1.0.0")
        
        # Update dataset status based on validation
        if contract.validation_status == "passed":
            db_dataset.status = DatasetStatus.PUBLISHED.value
            db_dataset.published_at = contract.created_at
        else:
            db_dataset.status = DatasetStatus.DRAFT.value
        
        db.commit()
        db.refresh(db_dataset)
        
    except Exception as e:
        # If contract creation fails, keep dataset in draft
        db_dataset.status = DatasetStatus.DRAFT.value
        db.commit()
        raise HTTPException(status_code=500, detail=f"Contract creation failed: {str(e)}")
    
    return db_dataset


@router.get("/")
def list_datasets(
    status: Optional[DatasetStatus] = None,
    classification: Optional[str] = None,
    owner_email: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    List all datasets with optional filtering.
    """
    query = db.query(Dataset).filter(Dataset.is_active == True)

    if status:
        query = query.filter(Dataset.status == status.value)

    if classification:
        query = query.filter(Dataset.classification == classification)

    if owner_email:
        query = query.filter(Dataset.owner_email == owner_email)

    datasets = query.offset(skip).limit(limit).all()

    # Enrich with computed fields
    result = []
    for dataset in datasets:
        dataset_dict = {
            'id': dataset.id,
            'name': dataset.name,
            'description': dataset.description,
            'owner_name': dataset.owner_name,
            'owner_email': dataset.owner_email,
            'source_type': dataset.source_type,
            'source_system': dataset.source_type,
            'physical_location': dataset.physical_location,
            'schema_definition': dataset.schema_definition,
            'schema': dataset.schema_definition,
            'classification': dataset.classification,
            'contains_pii': dataset.contains_pii,
            'compliance_tags': dataset.compliance_tags,
            'status': dataset.status,
            'is_active': dataset.is_active,
            'created_at': dataset.created_at,
            'updated_at': dataset.updated_at,
            'published_at': dataset.published_at,
            'subscriber_count': len([s for s in dataset.subscriptions if s.status == 'approved']),
        }

        # Add contract info if available
        if dataset.contracts:
            latest_contract = sorted(dataset.contracts, key=lambda c: c.created_at, reverse=True)[0]
            dataset_dict['contract'] = {
                'id': latest_contract.id,
                'version': latest_contract.version,
                'validation_result': latest_contract.validation_results if latest_contract.validation_results else {
                    'status': latest_contract.validation_status,
                    'passed': 0,
                    'failures': 0,
                    'warnings': 0,
                    'violations': []
                }
            }

        result.append(dataset_dict)

    return result


@router.get("/{dataset_id}")
def get_dataset(dataset_id: int, db: Session = Depends(get_db)):
    """
    Get a specific dataset by ID with enriched information.
    """
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.is_active == True).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # Build enriched response
    dataset_dict = {
        'id': dataset.id,
        'name': dataset.name,
        'description': dataset.description,
        'owner_name': dataset.owner_name,
        'owner_email': dataset.owner_email,
        'source_type': dataset.source_type,
        'source_system': dataset.source_type,
        'physical_location': dataset.physical_location,
        'schema_definition': dataset.schema_definition,
        'schema': dataset.schema_definition,
        'classification': dataset.classification,
        'contains_pii': dataset.contains_pii,
        'compliance_tags': dataset.compliance_tags,
        'status': dataset.status,
        'is_active': dataset.is_active,
        'created_at': dataset.created_at,
        'updated_at': dataset.updated_at,
        'published_at': dataset.published_at,
        'subscriber_count': len([s for s in dataset.subscriptions if s.status == 'approved']),
        'subscriptions': [
            {
                'id': s.id,
                'consumer_name': s.consumer_name,
                'status': s.status,
                'created_at': s.created_at
            } for s in dataset.subscriptions
        ]
    }

    # Add contract info if available
    if dataset.contracts:
        latest_contract = sorted(dataset.contracts, key=lambda c: c.created_at, reverse=True)[0]
        dataset_dict['contract'] = {
            'id': latest_contract.id,
            'version': latest_contract.version,
            'validation_result': latest_contract.validation_results if latest_contract.validation_results else {
                'status': latest_contract.validation_status,
                'passed': 0,
                'failures': 0,
                'warnings': 0,
                'violations': []
            }
        }

    return dataset_dict


@router.put("/{dataset_id}", response_model=DatasetResponse)
def update_dataset(dataset_id: int, dataset_update: DatasetUpdate, db: Session = Depends(get_db)):
    """
    Update a dataset and create a new contract version.
    """
    db_dataset = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.is_active == True).first()
    if not db_dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    # Track if schema changed
    schema_changed = False
    
    # Update fields
    if dataset_update.description is not None:
        db_dataset.description = dataset_update.description
    
    if dataset_update.owner_name is not None:
        db_dataset.owner_name = dataset_update.owner_name
    
    if dataset_update.owner_email is not None:
        db_dataset.owner_email = dataset_update.owner_email
    
    if dataset_update.schema_definition is not None:
        db_dataset.schema_definition = [field.dict() for field in dataset_update.schema_definition]
        schema_changed = True
        
        # Update PII flag
        contains_pii = any(field.pii for field in dataset_update.schema_definition)
        db_dataset.contains_pii = contains_pii
    
    if dataset_update.governance is not None:
        db_dataset.classification = dataset_update.governance.classification.value
        db_dataset.compliance_tags = dataset_update.governance.compliance_tags
    
    if dataset_update.status is not None:
        db_dataset.status = dataset_update.status.value
    
    db.commit()
    db.refresh(db_dataset)
    
    # Create new contract version if schema changed
    if schema_changed:
        try:
            # Get current max version
            from app.models.contract import Contract
            latest_contract = db.query(Contract).filter(
                Contract.dataset_id == dataset_id
            ).order_by(Contract.id.desc()).first()
            
            if latest_contract:
                # Increment major version for breaking changes
                old_version_parts = latest_contract.version.split('.')
                new_version = f"{int(old_version_parts[0]) + 1}.0.0"
            else:
                new_version = "1.0.0"
            
            contract_service.create_contract_from_dataset(db, db_dataset.id, version=new_version)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Contract update failed: {str(e)}")
    
    return db_dataset


@router.delete("/{dataset_id}", status_code=204)
def delete_dataset(dataset_id: int, db: Session = Depends(get_db)):
    """
    Soft delete a dataset (set is_active=False, status=deprecated).
    """
    db_dataset = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.is_active == True).first()
    if not db_dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    db_dataset.is_active = False
    db_dataset.status = DatasetStatus.DEPRECATED.value
    
    db.commit()
    return None


@router.post("/import-schema", response_model=SchemaImportResponse)
def import_schema(request: SchemaImportRequest):
    """
    Import schema from external data sources (PostgreSQL, files, Azure).
    """
    if request.source_type.value == "postgres":
        if not request.table_name:
            raise HTTPException(status_code=400, detail="table_name is required for postgres sources")
        
        try:
            # Initialize connector with optional connection string override
            if request.connection_string:
                # Parse connection string (simplified)
                connector = PostgresConnector()
                connector.connection = None  # Will use provided connection
            else:
                connector = PostgresConnector()
            
            # Test connection
            if not connector.test_connection():
                raise HTTPException(status_code=500, detail="Failed to connect to PostgreSQL database")
            
            # Import schema
            result = connector.import_table_schema(request.table_name, request.schema_name)
            
            return result
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Schema import failed: {str(e)}")
    
    elif request.source_type.value == "file":
        raise HTTPException(status_code=501, detail="File import not yet implemented")
    
    elif request.source_type.value in ["azure_blob", "azure_adls"]:
        raise HTTPException(status_code=501, detail="Azure import not yet implemented")
    
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported source type: {request.source_type}")


@router.get("/postgres/tables", response_model=List[TableInfo])
def list_postgres_tables(schema: str = Query("public")):
    """
    List all tables in PostgreSQL database.
    """
    try:
        connector = PostgresConnector()
        
        if not connector.test_connection():
            raise HTTPException(status_code=500, detail="Failed to connect to PostgreSQL database")
        
        tables = connector.list_tables(schema=schema)
        
        return tables
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list tables: {str(e)}")
