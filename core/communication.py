"""
Sistema de comunicación entre agentes.
Implementa el protocolo de comunicación y mensajería entre los diferentes agentes del sistema.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel
from loguru import logger
import asyncio
from queue import Queue

class Message(BaseModel):
    """Modelo de mensaje para la comunicación entre agentes"""
    id: str
    sender: str
    receiver: str
    content: Any
    type: str
    timestamp: datetime
    metadata: Dict = {}
    priority: int = 1
    in_response_to: Optional[str] = None

class CommunicationChannel:
    """Canal de comunicación entre agentes"""
    
    def __init__(self):
        """Inicializa el canal de comunicación"""
        self.message_queues: Dict[str, Queue] = {}
        self.subscribers: Dict[str, List[str]] = {}
        self.message_history: List[Message] = []
        logger.info("Canal de comunicación inicializado")
    
    def register_agent(self, agent_id: str):
        """Registra un nuevo agente en el sistema de comunicación"""
        if agent_id not in self.message_queues:
            self.message_queues[agent_id] = Queue()
            self.subscribers[agent_id] = []
            logger.info(f"Agente registrado: {agent_id}")
    
    def subscribe(self, subscriber_id: str, publisher_id: str):
        """Suscribe un agente para recibir mensajes de otro agente"""
        if publisher_id not in self.subscribers:
            self.subscribers[publisher_id] = []
        
        if subscriber_id not in self.subscribers[publisher_id]:
            self.subscribers[publisher_id].append(subscriber_id)
            logger.info(f"Agente {subscriber_id} suscrito a {publisher_id}")
    
    def send_message(self, message: Message):
        """Envía un mensaje a un agente específico"""
        if message.receiver not in self.message_queues:
            raise ValueError(f"Agente destino no encontrado: {message.receiver}")
            
        self.message_queues[message.receiver].put(message)
        self.message_history.append(message)
        logger.info(f"Mensaje enviado: {message.id} de {message.sender} a {message.receiver}")
        
        # Notificar a los suscriptores
        if message.sender in self.subscribers:
            for subscriber in self.subscribers[message.sender]:
                if subscriber != message.receiver:
                    notification = Message(
                        id=f"notif_{message.id}",
                        sender=message.sender,
                        receiver=subscriber,
                        content=f"Nuevo mensaje de {message.sender} a {message.receiver}",
                        type="notification",
                        timestamp=datetime.now(),
                        in_response_to=message.id
                    )
                    self.message_queues[subscriber].put(notification)
    
    def get_messages(self, agent_id: str, max_messages: int = 10) -> List[Message]:
        """Obtiene los mensajes pendientes para un agente"""
        if agent_id not in self.message_queues:
            raise ValueError(f"Agente no encontrado: {agent_id}")
            
        messages = []
        queue = self.message_queues[agent_id]
        
        for _ in range(max_messages):
            if queue.empty():
                break
            messages.append(queue.get())
            
        return messages
    
    def get_message_history(self, agent_id: str = None) -> List[Message]:
        """Obtiene el historial de mensajes, opcionalmente filtrado por agente"""
        if agent_id is None:
            return self.message_history
        
        return [
            msg for msg in self.message_history 
            if msg.sender == agent_id or msg.receiver == agent_id
        ]
    
    async def broadcast(self, sender: str, content: Any, type: str = "broadcast"):
        """Envía un mensaje a todos los agentes registrados"""
        timestamp = datetime.now()
        
        for receiver in self.message_queues.keys():
            if receiver != sender:
                message = Message(
                    id=f"broadcast_{len(self.message_history)}_{receiver}",
                    sender=sender,
                    receiver=receiver,
                    content=content,
                    type=type,
                    timestamp=timestamp
                )
                self.send_message(message)
                
        logger.info(f"Mensaje broadcast enviado por {sender}")
