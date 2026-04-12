from sqlalchemy.orm import Session
from fastapi import Request
from typing import Optional, Dict, Any
from datetime import datetime
import json
import logging

from infra.orm.AuditoriaModel import AuditoriaDB

logger = logging.getLogger(__name__)


class AuditoriaService:
    """Serviço para registrar auditoria de acessos e ações"""

    @staticmethod
    def registrar_acao(
        db: Session,
        funcionario_id: int,
        acao: str,
        recurso: str,
        recurso_id: Optional[int] = None,
        dados_antigos: Optional[Dict[str, Any]] = None,
        dados_novos: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None,
    ) -> bool:
        try:
            logger.info(f"Iniciando registro de auditoria - acao: {acao}, recurso: {recurso}")
            
            # Capturar informações da requisição
            ip_address = None
            user_agent = None
            if request:
                # IP do cliente
                forwarded_for = request.headers.get("X-Forwarded-For")
                if forwarded_for:
                    ip_address = forwarded_for.split(",")[0].strip()
                else:
                    ip_address = request.client.host
                # User Agent
                user_agent = request.headers.get("User-Agent")

            logger.info(f"IP: {ip_address}, User-Agent: {user_agent}")

            # Converter dados para JSON
            dados_novos_json = None
            if dados_novos:
                try:
                    logger.info(f"Convertendo dados_novos: {type(dados_novos)}")
                    if hasattr(dados_novos, "__table__"):
                        dados_novos_dict = {
                            column.name: getattr(dados_novos, column.name, None)
                            for column in dados_novos.__table__.columns
                        }
                        dados_novos_json = json.dumps(dados_novos_dict, default=str)
                    else:
                        dados_novos_json = json.dumps(dados_novos, default=str)
                    logger.info(f"dados_novos convertido com sucesso")
                except Exception as e:
                    logger.error(f"Erro ao serializar dados_novos: {e}", exc_info=True)
                    dados_novos_json = None

            dados_antigos_json = None
            if dados_antigos:
                try:
                    logger.info(f"Convertendo dados_antigos: {type(dados_antigos)}")
                    if hasattr(dados_antigos, "__table__"):
                        dados_antigos_dict = {
                            column.name: getattr(dados_antigos, column.name, None)
                            for column in dados_antigos.__table__.columns
                        }
                        dados_antigos_json = json.dumps(dados_antigos_dict, default=str)
                    else:
                        dados_antigos_json = json.dumps(dados_antigos, default=str)
                    logger.info(f"dados_antigos convertido com sucesso")
                except Exception as e:
                    logger.error(f"Erro ao serializar dados_antigos: {e}", exc_info=True)
                    dados_antigos_json = None

            logger.info(f"Criando registro de auditoria...")
            # Criar registro de auditoria
            auditoria = AuditoriaDB(
                funcionario_id=funcionario_id,
                acao=acao,
                recurso=recurso,
                recurso_id=recurso_id,
                dados_antigos=dados_antigos_json,
                dados_novos=dados_novos_json,
                ip_address=ip_address,
                user_agent=user_agent,
                data_hora=datetime.now(),
            )
            db.add(auditoria)
            db.commit()
            logger.info(f"Auditoria registrada com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao registrar auditoria: {e}", exc_info=True)
            db.rollback()
            return False