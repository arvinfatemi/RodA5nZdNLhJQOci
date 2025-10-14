"""
API endpoints for report generation and delivery.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse

from app.models.reporting import WeeklyReportData, ReportDeliveryStatus
from app.services.report_service import report_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/weekly/send", response_model=ReportDeliveryStatus)
async def send_weekly_report_now(
    recipient_override: Optional[str] = Query(None, description="Override default email recipient")
):
    """
    Manually trigger weekly report send (for testing).

    This endpoint immediately generates and sends a weekly report email.
    Useful for testing the report generation and email delivery.
    """
    try:
        delivery_status = await report_service.send_weekly_email_report(
            recipient_override=recipient_override
        )
        return delivery_status

    except Exception as e:
        logger.error(f"Failed to send weekly report: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send report: {str(e)}")


@router.get("/weekly/preview", response_model=WeeklyReportData)
async def preview_weekly_report(
    days: int = Query(7, description="Number of days to include in report", ge=1, le=30)
):
    """
    Preview weekly report data (JSON format).

    Returns the structured data that would be included in the weekly report.
    Useful for debugging and understanding what data is available.
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        report_data = await report_service.generate_weekly_report_data(
            start_date=start_date,
            end_date=end_date
        )

        return report_data

    except Exception as e:
        logger.error(f"Failed to generate report preview: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate preview: {str(e)}")


@router.get("/weekly/html", response_class=HTMLResponse)
async def preview_weekly_report_html(
    days: int = Query(7, description="Number of days to include in report", ge=1, le=30)
):
    """
    Preview weekly report HTML.

    Returns the rendered HTML that would be sent in the email.
    Useful for testing the email template rendering and styling.
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Generate report data
        report_data = await report_service.generate_weekly_report_data(
            start_date=start_date,
            end_date=end_date
        )

        # Generate HTML
        html_content = await report_service.generate_report_html(report_data)

        return HTMLResponse(content=html_content, status_code=200)

    except Exception as e:
        logger.error(f"Failed to generate HTML preview: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate HTML: {str(e)}")


@router.get("/weekly/plain-text")
async def preview_weekly_report_plain_text(
    days: int = Query(7, description="Number of days to include in report", ge=1, le=30)
):
    """
    Preview weekly report in plain text format.

    Returns the plain text version that would be included as email fallback.
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Generate report data
        report_data = await report_service.generate_weekly_report_data(
            start_date=start_date,
            end_date=end_date
        )

        # Generate plain text
        plain_text = report_service._generate_plain_text(report_data)

        return JSONResponse(content={"plain_text": plain_text})

    except Exception as e:
        logger.error(f"Failed to generate plain text preview: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate plain text: {str(e)}")


@router.get("/config")
async def get_report_config():
    """
    Get current report configuration from Google Sheets.

    Returns the configuration for automated reports including
    schedule, enabled status, and recipient information.
    """
    try:
        from app.services.config_service import config_service

        config_response = await config_service.fetch_config()

        if not config_response.get("success"):
            raise HTTPException(status_code=500, detail="Failed to fetch configuration")

        sheet_config = config_response["config"]

        report_config = {
            "enable_email_reports": sheet_config.get("enable_email_reports", True),
            "report_day": sheet_config.get("report_day", "monday"),
            "report_time": sheet_config.get("report_time", "09:00"),
            "email_configured": bool(
                sheet_config.get("email_smtp_host") or
                getattr(__import__('app.config').config.settings, 'email_smtp_host', None)
            ),
        }

        return JSONResponse(content=report_config)

    except Exception as e:
        logger.error(f"Failed to get report config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get config: {str(e)}")
