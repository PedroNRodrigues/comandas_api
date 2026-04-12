from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import timedelta

from domain.schemas.AuthSchema import (
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    FuncionarioAuth,
)

from infra.orm.FuncionarioModel import FuncionarioDB
from infra.database import get_db
from infra.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
)
from infra.dependencies import get_current_active_user
from services.AuditoriaService import AuditoriaService
from infra.rate_limit import limiter, get_rate_limit

from settings import ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_TOKEN_EXPIRE_DAYS

router = APIRouter()


@router.post(
    "/auth/login",
    response_model=TokenResponse,
    tags=["Autenticação"],
    summary="Login de funcionário - pública - retorna access e refresh token",
)
@limiter.limit(get_rate_limit("critical"))
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db),
    request: Request = None,
):
    """
    Realiza login do funcionário e retorna access token e refresh token

    - **cpf**: CPF do funcionário
    - **senha**: Senha do funcionário

    Retorna:
    - access_token: Token de curta duração (15 minutos)
    - refresh_token: Token de longa duração (7 dias)
    """
    try:
        # Busca funcionário pelo CPF
        funcionario = (
            db.query(FuncionarioDB).filter(FuncionarioDB.cpf == login_data.cpf).first()
        )

        if not funcionario:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="CPF ou senha inválidos",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verifica se a senha está correta
        if not verify_password(login_data.senha, funcionario.senha):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="CPF ou senha inválidos",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Cria o access token JWT (curta duração)
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "sub": funcionario.cpf,
                "id": funcionario.id,
                "grupo": funcionario.grupo,
            },
            expires_delta=access_token_expires,
        )

        # Cria o refresh token JWT (longa duração)
        refresh_token = create_refresh_token(
            data={
                "sub": funcionario.cpf,
                "id": funcionario.id,
                "grupo": funcionario.grupo,
            }
        )

        # Registrar auditoria de login
        AuditoriaService.registrar_acao(
            db=db,
            funcionario_id=funcionario.id,
            acao="LOGIN",
            recurso="AUTH",
            request=request,
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            refresh_expires_in=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao realizar login: {str(e)}",
        )