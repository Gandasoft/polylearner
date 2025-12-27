"""
Google Calendar API integration service
"""
import httpx
from datetime import datetime
from typing import List, Optional, Dict, Any


class CalendarService:
    """Service for interacting with Google Calendar API"""
    
    CALENDAR_API_BASE = "https://www.googleapis.com/calendar/v3"
    
    def __init__(self, access_token: str):
        """
        Initialize the calendar service with user's access token
        
        Args:
            access_token: Google OAuth access token with calendar permissions
        """
        self.access_token = access_token
        self.headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
    
    async def list_calendars(self) -> List[Dict[str, Any]]:
        """
        List all calendars accessible to the user
        
        Returns:
            List of calendar objects
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.CALENDAR_API_BASE}/users/me/calendarList",
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            return data.get('items', [])
    
    async def create_event(
        self,
        summary: str,
        start_time: datetime,
        end_time: datetime,
        description: Optional[str] = None,
        calendar_id: str = 'primary',
        timezone: str = 'UTC'
    ) -> Dict[str, Any]:
        """
        Create a new calendar event
        
        Args:
            summary: Event title
            start_time: Event start datetime
            end_time: Event end datetime
            description: Optional event description
            calendar_id: Calendar ID (default: 'primary')
            timezone: Timezone for the event
            
        Returns:
            Created event object
        """
        event_data = {
            'summary': summary,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': timezone,
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': timezone,
            }
        }
        
        if description:
            event_data['description'] = description
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.CALENDAR_API_BASE}/calendars/{calendar_id}/events",
                headers=self.headers,
                json=event_data
            )
            response.raise_for_status()
            return response.json()
    
    async def update_event(
        self,
        event_id: str,
        summary: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        description: Optional[str] = None,
        calendar_id: str = 'primary',
        timezone: str = 'UTC'
    ) -> Dict[str, Any]:
        """
        Update an existing calendar event
        
        Args:
            event_id: ID of the event to update
            summary: Optional new event title
            start_time: Optional new start datetime
            end_time: Optional new end datetime
            description: Optional new description
            calendar_id: Calendar ID (default: 'primary')
            timezone: Timezone for the event
            
        Returns:
            Updated event object
        """
        # First, get the existing event
        async with httpx.AsyncClient() as client:
            get_response = await client.get(
                f"{self.CALENDAR_API_BASE}/calendars/{calendar_id}/events/{event_id}",
                headers=self.headers
            )
            get_response.raise_for_status()
            event_data = get_response.json()
        
        # Update only the provided fields
        if summary:
            event_data['summary'] = summary
        if start_time:
            event_data['start'] = {
                'dateTime': start_time.isoformat(),
                'timeZone': timezone,
            }
        if end_time:
            event_data['end'] = {
                'dateTime': end_time.isoformat(),
                'timeZone': timezone,
            }
        if description:
            event_data['description'] = description
        
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.CALENDAR_API_BASE}/calendars/{calendar_id}/events/{event_id}",
                headers=self.headers,
                json=event_data
            )
            response.raise_for_status()
            return response.json()
    
    async def delete_event(
        self,
        event_id: str,
        calendar_id: str = 'primary'
    ) -> None:
        """
        Delete a calendar event
        
        Args:
            event_id: ID of the event to delete
            calendar_id: Calendar ID (default: 'primary')
        """
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.CALENDAR_API_BASE}/calendars/{calendar_id}/events/{event_id}",
                headers=self.headers
            )
            response.raise_for_status()
    
    async def list_events(
        self,
        calendar_id: str = 'primary',
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None,
        max_results: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List events in a calendar
        
        Args:
            calendar_id: Calendar ID (default: 'primary')
            time_min: Optional minimum time for events
            time_max: Optional maximum time for events
            max_results: Maximum number of events to return
            
        Returns:
            List of event objects
        """
        params = {
            'maxResults': max_results,
            'singleEvents': True,
            'orderBy': 'startTime'
        }
        
        if time_min:
            params['timeMin'] = time_min.isoformat() + 'Z'
        if time_max:
            params['timeMax'] = time_max.isoformat() + 'Z'
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.CALENDAR_API_BASE}/calendars/{calendar_id}/events",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            data = response.json()
            return data.get('items', [])
    
    async def batch_create_events(
        self,
        events: List[Dict[str, Any]],
        calendar_id: str = 'primary'
    ) -> List[Dict[str, Any]]:
        """
        Create multiple events in batch
        
        Args:
            events: List of event data dictionaries
            calendar_id: Calendar ID (default: 'primary')
            
        Returns:
            List of created event objects
        """
        created_events = []
        for event in events:
            created_event = await self.create_event(
                summary=event['summary'],
                start_time=event['start_time'],
                end_time=event['end_time'],
                description=event.get('description'),
                calendar_id=calendar_id,
                timezone=event.get('timezone', 'UTC')
            )
            created_events.append(created_event)
        return created_events
