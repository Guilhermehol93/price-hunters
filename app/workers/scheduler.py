"""Periodic Task Scheduler using APScheduler"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.workers.task_worker import run_worker_cycle

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def start_scheduler():
    logger.info("Configurando agendador de tarefas periódicas...")
    # Executa a verificação de monitoramentos a cada 2 minutos
    scheduler.add_job(
        run_worker_cycle,
        "interval",
        minutes=2,
        id="monitoring_check_job",
        replace_existing=True
    )
    scheduler.start()
    logger.info("Agendador de tarefas iniciado com sucesso.")


def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Agendador de tarefas finalizado.")
