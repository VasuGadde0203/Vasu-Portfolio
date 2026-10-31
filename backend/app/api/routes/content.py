from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.knowledge import public_profile
from app.schemas.content import Profile, Project

router = APIRouter(tags=["content"])


@router.get("/profile", response_model=Profile, response_model_exclude={"comment": True, "contact": {"note"}})
def get_profile(request: Request) -> Profile:
    return public_profile(request.app.state.profile)


@router.get("/projects", response_model=list[Project])
def list_projects(request: Request) -> list[Project]:
    return request.app.state.projects


@router.get("/projects/{project_id}", response_model=Project)
def get_project(project_id: str, request: Request) -> Project:
    for project in request.app.state.projects:
        if project.id == project_id:
            return project
    raise HTTPException(status_code=404, detail="Project not found")
