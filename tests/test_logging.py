import asyncio
import json 
import shutil
from pathlib import Path
from uuid import uuid4
import logging
from logging.handlers import RotatingFileHandler

from bus.event_bus import EventBus
from events.speech import TranscriptGenerated
from events.events import PipelineStartEvent
from services.logging import LoggingService
from store.sqlite_store import SQLiteEventStore


async def main()->None:
    
    test_run_id = uuid4().hex[:8]
    test_log_dir = Path(f"test_logs_{test_run_id}")
    test_log_file = test_log_dir / "orion_test.log"
    test_db_file = Path(f"test_logging_{test_run_id}.db")

    print("Init test db and event bus ...")
    store = SQLiteEventStore(str(test_db_file))
    await store.initialize()
    bus = EventBus(store)

    log_dir = ""
    


    print("Starting LoggingService in test mode...")
    logging_service = LoggingService(
        log_dir = test_log_dir,
        log_file = test_log_file,
    )
    await logging_service.startup()


    bus.subscribe_all(logging_service.handle)

    correlation_id = uuid4()

    print("Publish pipeline start event...")
    event_start = PipelineStartEvent(
        correlation_id=correlation_id,
        source="test_runner",
        message = "Logging test pipeline start",
    )
    await bus.publish(event_start)
    print("Publishing   TranscriptGenerated...")                                                                   
    event_trans = TranscriptGenerated(                                                                           
            correlation_id=correlation_id,                                                                           
            source="stt_test",                                                                                       
            text="Hello Orion, verifying disk logging system.",                                                      
        )                                                                                                            
    await bus.publish(event_trans)                                                                               
                                                                                                                     
        # Allow a short delay for background thread disk writes to complete                                          
    await asyncio.sleep(0.5)                                                                                     
                                                                                                                     
    print("\n--- Verifying Logs on Disk ---")                                                                    
    if not test_log_file.exists():                                                                               
            print("❌ Test Failed: Log file was not created!")                                                       
            return                                                                                                   
                                                                                                                     
    with open(test_log_file, "r", encoding="utf-8") as f:                                                        
            log_lines = f.readlines()                                                                                
                                                                                                                     
    if len(log_lines) != 2:                                                                                      
            print(f"❌ Test Failed: Expected 2 log lines, but got {len(log_lines)}")                                 
            return                                                                                                   
                                                                                                                     
        # Check properties of PipelineStartEvent                                                                     
    log_entry_1 = json.loads(log_lines[0].strip())                                                               
    print(f"Log Line 1: {log_entry_1}")                                                                          
    assert log_entry_1["event_type"] == "PipelineStartEvent"                                                     
    assert log_entry_1["source"] == "test_runner"                                                                
    assert log_entry_1["message"] == "Logging test pipeline start"                                            
    assert "status" not in log_entry_1  # 'status' is base metadata, not expected at top level or payload        
    print("✓ PipelineStartEvent fields verified.")                                                               
                                                                                                                     
        # Check properties of TranscriptGenerated                                                                    
    log_entry_2 = json.loads(log_lines[1].strip())                                                               
    print(f"Log Line 2: {log_entry_2}")                                                                          
    assert log_entry_2["event_type"] == "TranscriptGenerated"                                                    
    assert log_entry_2["source"] == "stt_test"                                                                   
    assert log_entry_2["payload"]["text"] == "Hello Orion, verifying disk logging system."                       
    print("✓ TranscriptGenerated fields & payload verified.")                                                    
                                                                                                                     
    print("\n✅ All tests passed successfully!")                                                                 
                                                                                                                     
        # Cleanup and Shutdown                                                                                       
    await logging_service.shutdown()                                                                             
    await store.close()                                                                                          
                                                                                                                     
    if test_log_dir.exists():                                                                                    
            shutil.rmtree(test_log_dir)                                                                              
            print("Cleaned up test log directory.")                                                                  
    if test_db_file.exists():                                                                                    
            test_db_file.unlink()                                                                                    
            print("Cleaned up test database file.")                                                                  
                                                                                                                     
                                                                                                                     
if __name__ == "__main__":
    asyncio.run(main())                                                                                          
                                                    
