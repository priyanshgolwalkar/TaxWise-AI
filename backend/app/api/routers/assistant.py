from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.conversation import Conversation, Message
from app.models.user import User
from app.schemas.common import AssistantRequest
from app.services.assistant import AIProviderError, get_ai_service

router = APIRouter(prefix='/assistant', tags=['ai assistant'])

@router.get('/conversations')
def list_conversations(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	rows = db.query(Conversation).filter(Conversation.user_id == user.id).order_by(Conversation.updated_at.desc()).all()
	return [{'id': row.id, 'created_at': row.created_at, 'updated_at': row.updated_at, 'title': next((message.content for message in row.messages if message.role == 'user'), 'New conversation')[:72]} for row in rows]

@router.post('/conversations', status_code=201)
def create_conversation(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	conversation = Conversation(user_id=user.id)
	db.add(conversation); db.commit(); db.refresh(conversation)
	return {'id': conversation.id, 'created_at': conversation.created_at, 'updated_at': conversation.updated_at, 'messages': []}

@router.get('/conversations/{conversation_id}/messages', responses={404: {'description': 'Conversation not found'}})
def list_messages(conversation_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
	conversation = db.query(Conversation).filter(Conversation.id == conversation_id, Conversation.user_id == user.id).first()
	if conversation is None:
		raise HTTPException(status_code=404, detail='Conversation not found')
	return [{'id': row.id, 'role': row.role, 'content': row.content, 'created_at': row.created_at} for row in conversation.messages]

@router.post('/chat', responses={404: {'description': 'Conversation not found'}, 503: {'description': 'Hosted AI provider unavailable'}})
async def chat(payload: AssistantRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
	if payload.conversation_id:
		conversation = db.query(Conversation).filter(Conversation.id == payload.conversation_id, Conversation.user_id == user.id).first()
		if conversation is None:
			raise HTTPException(status_code=404, detail='Conversation not found')
	else:
		conversation = Conversation(user_id=user.id)
		db.add(conversation); db.flush()
	history_rows = db.query(Message).filter(Message.conversation_id == conversation.id).order_by(Message.created_at.asc()).limit(20).all()
	history = [{'role': row.role, 'content': row.content} for row in history_rows]
	db.add(Message(conversation_id=conversation.id, role='user', content=payload.message))
	db.commit()
	try:
		answer, sources = await get_ai_service().respond(db, user, payload.message, history)
	except AIProviderError as exc:
		raise HTTPException(status_code=503, detail=str(exc)) from exc
	db.add(Message(conversation_id=conversation.id, role='assistant', content=answer))
	conversation.updated_at = datetime.now()
	db.commit(); db.refresh(conversation)
	return {'answer': answer, 'conversation_id': conversation.id, 'sources': sources}
