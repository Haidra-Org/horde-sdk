# horde_sdk specific definitions

## API 

### Clients

#### ManualClient

A manual client interacts with an API but does not provide any context management. Clients of this kind do not automatically cancel in-process jobs, for example.

#### ClientSession

Client session classes provide context management for API operations. They automatically cancel or follow-up on any in-process operations when exiting the context. Client sessions generally inherit from ManualClient.
