"""
Proactive agents module for scheduled task execution.
"""
import asyncio
import logging
from typing import Dict, Any, Optional
from apscheduler.schedulers.background import BackgroundScheduler

from src.database.models import DatabaseManager
from config.settings import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProactiveAgentManager:
    """Manager for proactive agents that run scheduled tasks"""
    
    def __init__(self, db_manager: DatabaseManager = None):
        self.db_manager = db_manager or DatabaseManager()
        self._scheduler: Optional[BackgroundScheduler] = None
        self._jobs: Dict[str, Any] = {}
        
    @property
    def scheduler(self) -> BackgroundScheduler:
        """Get or create the background scheduler"""
        if self._scheduler is None:
            self._scheduler = BackgroundScheduler()
            self._scheduler.start()
        return self._scheduler
    
    async def _execute_agent_task(self, name: str, prompt: str, agent_obj: Any, retries: int = 2) -> None:
        """Execute a proactive agent task"""
        attempt = 0
        
        while attempt <= retries:
            try:
                logger.info(f"Executing proactive agent '{name}' - attempt {attempt + 1}")
                
                # Run the agent with the configured max steps
                config = Config()
                response = await agent_obj.run(
                    f"Proactive Task Prompt: {prompt}", 
                    max_steps=config.MAX_AGENT_STEPS
                )
                
                # Save successful execution
                self.db_manager.save_message(
                    "assistant", 
                    f"🔔 [{name}] Proactive Update:\\n{response}"
                )
                self.db_manager.save_tool_log(name, f"Prompt executed: {prompt}")
                self.db_manager.update_proactive_agent_last_run(name)
                
                logger.info(f"Proactive agent '{name}' executed successfully")
                break
                
            except Exception as e:
                error_msg = f"⚠️ [{name}] Proactive Check Error (Attempt {attempt+1}): {str(e)}"
                logger.error(error_msg)
                
                self.db_manager.save_message("assistant", error_msg)
                attempt += 1
                
                if attempt <= retries:
                    await asyncio.sleep(5)  # Wait before retry
    
    def _create_job_wrapper(self, name: str, prompt: str, agent_obj: Any, retries: int = 2):
        """Create a wrapper function for the scheduler job"""
        def run_async_job():
            try:
                # Try to run in existing event loop
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Create a task in the existing loop
                    asyncio.create_task(
                        self._execute_agent_task(name, prompt, agent_obj, retries)
                    )
                else:
                    # Run in new event loop
                    asyncio.run(
                        self._execute_agent_task(name, prompt, agent_obj, retries)
                    )
            except RuntimeError:
                # Fallback: create new event loop
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(
                        self._execute_agent_task(name, prompt, agent_obj, retries)
                    )
                    loop.close()
                except Exception as e:
                    logger.error(f"Failed to execute proactive agent '{name}': {e}")
        
        return run_async_job
    
    def add_proactive_agent(self, name: str, interval_minutes: int, prompt: str, 
                          agent_obj: Any, retries: int = 2) -> None:
        """
        Add a proactive agent that runs periodically.
        
        Args:
            name: Unique name for the agent
            interval_minutes: Interval between executions in minutes
            prompt: Prompt to execute
            agent_obj: Agent object to run the prompt
            retries: Number of retries on failure
        """
        # Save agent configuration to database
        self.db_manager.save_proactive_agent(name, prompt, interval_minutes)
        
        # Remove existing job if any
        if name in self._jobs:
            self.scheduler.remove_job(name)
        
        # Create and schedule new job
        job_wrapper = self._create_job_wrapper(name, prompt, agent_obj, retries)
        job = self.scheduler.add_job(
            job_wrapper, 
            'interval', 
            minutes=interval_minutes, 
            id=name,
            replace_existing=True
        )
        
        self._jobs[name] = job
        logger.info(f"Added proactive agent '{name}' with {interval_minutes} minute interval")
    
    def remove_proactive_agent(self, name: str) -> None:
        """Remove a proactive agent"""
        if name in self._jobs:
            self.scheduler.remove_job(name)
            del self._jobs[name]
            logger.info(f"Removed proactive agent '{name}'")
        
        # Remove from database
        self.db_manager.delete_proactive_agent(name)
    
    def pause_proactive_agent(self, name: str) -> None:
        """Pause a proactive agent"""
        if name in self._jobs:
            self.scheduler.pause_job(name)
            logger.info(f"Paused proactive agent '{name}'")
    
    def resume_proactive_agent(self, name: str) -> None:
        """Resume a proactive agent"""
        if name in self._jobs:
            self.scheduler.resume_job(name)
            logger.info(f"Resumed proactive agent '{name}'")
    
    def get_agent_status(self, name: str) -> Dict[str, Any]:
        """Get status of a proactive agent"""
        if name in self._jobs:
            job = self.scheduler.get_job(name)
            if job:
                return {
                    "name": name,
                    "next_run": job.next_run_time,
                    "active": True
                }
        
        return {
            "name": name,
            "next_run": None,
            "active": False
        }
    
    def list_active_agents(self) -> Dict[str, Dict[str, Any]]:
        """List all active proactive agents"""
        agents = {}
        for name in self._jobs.keys():
            agents[name] = self.get_agent_status(name)
        return agents
    
    def shutdown(self) -> None:
        """Shutdown the scheduler and cleanup resources"""
        if self._scheduler:
            self._scheduler.shutdown()
            self._jobs.clear()
            logger.info("Proactive agent manager shutdown completed")


# Global manager instance
_global_manager = None


def get_manager() -> ProactiveAgentManager:
    """Get or create global proactive agent manager"""
    global _global_manager
    if _global_manager is None:
        _global_manager = ProactiveAgentManager()
    return _global_manager


# Legacy functions for backward compatibility
def add_proactive_agent(name: str, interval_minutes: int, prompt: str, agent_obj: Any, retries: int = 2):
    """Add proactive agent (legacy function)"""
    manager = get_manager()
    manager.add_proactive_agent(name, interval_minutes, prompt, agent_obj, retries)


def remove_proactive_agent(name: str):
    """Remove proactive agent (legacy function)"""
    manager = get_manager()
    manager.remove_proactive_agent(name)