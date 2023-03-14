from enum import Enum
from enum import unique

import pandas
from fastapi import UploadFile

from apps.entities.base import BaseValidator
from apps.entities.imports.schemas import TeamMetricCSV
from core.exceptions import BadRequestException


@unique
class ImportErrors(Enum):
    invalid_file = "Invalid file"
    missing_columns = "Missing columns in file"
    duplicated_data = "File contains duplicates"
    empty_file = "Empty file"


@unique
class ImportFileColumns(Enum):
    date = "date"
    review_time = "review_time"
    team = "team"
    merge_time = "merge_time"


class ImportValidator(BaseValidator):
    async def validate_create(self, file: UploadFile) -> tuple[list[TeamMetricCSV], set[str]]:
        try:
            df = pandas.read_csv(file.file)
        except Exception:
            raise BadRequestException(ImportErrors.invalid_file)
        for f in ImportFileColumns:
            if f.value not in df.columns:
                raise BadRequestException(ImportErrors.missing_columns)
        if df[[ImportFileColumns.date.value, ImportFileColumns.team.value]].duplicated().any():
            raise BadRequestException(ImportErrors.duplicated_data)
        if len(df) == 0:
            raise BadRequestException(ImportErrors.empty_file)
        results, teams = [], set()
        for row in df.to_dict("records"):
            try:
                entry = TeamMetricCSV(**row)  # pydantic might be slow, so we can validate with another library
            except Exception as e:
                raise BadRequestException(f"Unable to process data: {str(e)}")
            teams.add(entry.team)
            results.append(entry)

        return results, teams
