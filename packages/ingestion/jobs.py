from packages.ingestion.contracts import DocumentIngestionJobRecord, IngestionJobStatus


class DocumentIngestionJobs:
    def start_job(
        self,
        job: DocumentIngestionJobRecord,
    ) -> DocumentIngestionJobRecord:
        return DocumentIngestionJobRecord(
            job_id=job.job_id,
            document_id=job.document_id,
            tenant_id=job.tenant_id,
            version=job.version,
            status=IngestionJobStatus.PROCESSING,
        )

    def complete_job(
        self,
        job: DocumentIngestionJobRecord,
    ) -> DocumentIngestionJobRecord:
        return DocumentIngestionJobRecord(
            job_id=job.job_id,
            document_id=job.document_id,
            tenant_id=job.tenant_id,
            version=job.version,
            status=IngestionJobStatus.COMPLETED,
        )

    def fail_job(
        self,
        job: DocumentIngestionJobRecord,
    ) -> DocumentIngestionJobRecord:
        return DocumentIngestionJobRecord(
            job_id=job.job_id,
            document_id=job.document_id,
            tenant_id=job.tenant_id,
            version=job.version,
            status=IngestionJobStatus.FAILED,
        )