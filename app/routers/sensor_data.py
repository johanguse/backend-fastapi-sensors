import csv
from datetime import datetime
from io import StringIO

import chardet
import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, Body
from fastapi_pagination import LimitOffsetPage
from sqlalchemy.orm import Session

from app.core.auth import get_current_admin_user, get_current_user
from app.core.database import get_db
from app.models.equipment import Equipment
from app.models.sensor_data import SensorData as SensorDataModel
from app.models.user import User, user_company
from app.schemas.sensor_data import SensorDataOut, SensorDataBase

router = APIRouter()


@router.get('/sensor-data', response_model=LimitOffsetPage[SensorDataOut])
def read_sensor_data(
    equipment_id: int = Query(..., description='Filter by equipment ID'),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    equipment = (
        db.query(Equipment).filter(Equipment.id == equipment_id).first()
    )
    if not equipment:
        raise HTTPException(status_code=404, detail='Equipment not found')

    user_company_relation = (
        db.query(user_company)
        .filter(
            user_company.c.user_id == current_user.id,
            user_company.c.company_id == equipment.company_id,
        )
        .first()
    )

    if not user_company_relation:
        raise HTTPException(
            status_code=403,
            detail="User does not have access to this equipment's data",
        )

    query = db.query(SensorDataModel)
    query = query.filter(SensorDataModel.equipment_id == equipment_id)

    total = query.count()
    items = (
        query.order_by(SensorDataModel.timestamp.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return LimitOffsetPage(
        items=items, total=total, limit=limit, offset=offset
    )


def detect_delimiter(file_content: str):
    sniffer = csv.Sniffer()
    try:
        dialect = sniffer.sniff(file_content)
        return dialect.delimiter
    except csv.Error:
        return ','

@router.post('/sensor-data', response_model=SensorDataOut)
def create_sensor_data(
    sensor_data: SensorDataBase = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    equipment = db.query(Equipment).filter(Equipment.equipment_id == sensor_data.equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=404, detail=f"Equipment with ID {sensor_data.equipment_id} not found")

    user_company_relation = (
        db.query(user_company)
        .filter(
            user_company.c.user_id == current_user.id,
            user_company.c.company_id == equipment.company_id,
        )
        .first()
    )
    if not user_company_relation:
        raise HTTPException(
            status_code=403,
            detail=f"You don't have access to equipment {sensor_data.equipment_id}",
        )

    new_sensor_data = SensorDataModel(
        equipment_id=equipment.id,
        timestamp=sensor_data.timestamp,
        value=sensor_data.value,
    )

    db.add(new_sensor_data)
    db.commit()
    db.refresh(new_sensor_data)

    return new_sensor_data

@router.post('/upload-csv/')
async def upload_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=400,
            detail='File format not supported. Please upload a CSV file.',
        )

    contents = await file.read()
    result = chardet.detect(contents)
    file_encoding = (
        result['encoding'] if result['encoding'] is not None else 'utf-8'
    )

    try:
        decoded_contents = contents.decode(file_encoding)
        delimiter = detect_delimiter(decoded_contents)
        df = pd.read_csv(StringIO(decoded_contents), delimiter=delimiter)
        df.columns = df.columns.str.strip()

        required_columns = ['equipmentId', 'timestamp', 'value']
        if not all(column in df.columns for column in required_columns):
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {', '.join(required_columns)}",
            )

        sensor_data_list = []
        for index, row in df.iterrows():
            try:
                timestamp_dt = datetime.strptime(
                    row['timestamp'].strip(), '%Y-%m-%dT%H:%M:%S.%f%z'
                )

                equipment = (
                    db.query(Equipment)
                    .filter(Equipment.equipment_id == row['equipmentId'])
                    .first()
                )
                if not equipment:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Equipment with ID {row['equipmentId']} not found",
                    )

                user_company_relation = (
                    db.query(user_company)
                    .filter(
                        user_company.c.user_id == current_user.id,
                        user_company.c.company_id == equipment.company_id,
                    )
                    .first()
                )
                if not user_company_relation:
                    raise HTTPException(
                        status_code=403,
                        detail=f"You don't have access to equipment {row['equipmentId']}",
                    )

                sensor_data = SensorDataModel(
                    equipment_id=equipment.id,
                    timestamp=timestamp_dt,
                    value=float(row['value']),
                )
                sensor_data_list.append(sensor_data)
            except ValueError as ve:
                raise HTTPException(
                    status_code=400,
                    detail=f'Error processing row {index}: {str(ve)}',
                )

        db.bulk_save_objects(sensor_data_list)
        db.commit()

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail='Could not decode file content. Please ensure the file is properly encoded.',
        )
    except pd.errors.ParserError:
        raise HTTPException(
            status_code=400,
            detail='Error parsing the CSV file. Please check the file format.',
        )

    return {
        'detail': 'File processed successfully',
        'sensors_added': len(sensor_data_list),
    }
