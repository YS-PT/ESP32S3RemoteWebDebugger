# ESP32S3RemoteWebDebugger
 
A Web-Based Remote Debugging Dashboard for the ESP32-S3 microcontroller, which allows users to upload, debug, and flash firmware via a web browser. 
The core novelty of the system lies in its integration of OpenOCD and GDB debugging protocols into a real-time, browser-accessible interface using Flask and Socket.IO. This setup enables students to initiate and monitor code execution through GDB, issue Telnet commands for memory flashing, and interact with hardware remotely. 

The project demonstrates a practical and modular architecture using Flask and Socket.IO, enhancing accessibility while maintaining system-level control through JTAG and serial interfaces.

**Methodlogy**
![image](https://github.com/user-attachments/assets/c19cf01e-46fa-4d6b-8f23-9b3131cd5bd6)

**Technology used**

JavaScript : runs in the browser, makes websites interactive

Python : runs on the server, handles logic, data, and control

![image](https://github.com/user-attachments/assets/30af272d-db62-4518-a8cd-f89d6e8dd6a4)

**Here’s how Flask and JavaScript work together in this project:**
![image](https://github.com/user-attachments/assets/6f5ab4d5-de27-4c63-84d3-aa6453ba7971)

**Web Debugger Architecture**
![image](https://github.com/user-attachments/assets/4a70d9c4-b1f2-4d13-abf9-9bebc62d9e63)


**Unique Innovation**

- Web-based debugging via OpenOCD (Real time Debugging via GDB + Telnet)
- No Complex local Toolchain required Browser only
- VPN-backed secure remote access (Tailscale:secure, peer-to peer connection, simplified setup while ensuring encrypted access)
- Location freedom
