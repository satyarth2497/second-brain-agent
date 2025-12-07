# Real-Time Meeting Transcription  
### Topic: Email Notification Tool Architecture (AWS)  
### Date: Feb 12, 2025  
### Duration: 41 minutes  
### Participants:  
- **Alice – Lead Architect**  
- **Bob – Backend Engineer**  
- **Priya – DevOps Engineer**  
- **Sam – Product Manager**  
- **David – Security Engineer**  

---

## 00:00 – Meeting Start
**Sam:** Morning, everyone. Today’s goal is to finalize the architecture for the Email Notification Tool that will be used across our internal services. Requirements: reliable delivery, scalable, supports templating, logs, retries, and ideally SMS later.

**Alice:** Perfect. Let’s walk through the AWS components.

---

## 02:10 – High-Level Architecture Discussion
**Alice:** At a high level, I propose:  
- Use **SNS** as entry point  
- **Lambda worker** for processing  
- **SES** for sending emails  
- **CloudWatch** + **S3** for logging  
- **SQS DLQ** for failures  
- Templating via **S3** or **SES Template Store**

**Bob:** Why SNS instead of SQS directly?

**Alice:** SNS gives pub/sub flexibility for SMS or push notifications later.

---

## 05:45 – Event Flow Walkthrough
**Priya:** Event flow proposal:

1. Microservice publishes → **SNS Topic: NotificationsTopic**  
2. SNS pushes to **SQS Queue**  
3. **SQS triggers Lambda EmailSender**  
4. Lambda loads template from **S3/templates/**  
5. Lambda personalizes template  
6. Lambda calls **SES::SendEmail**  
7. Success logged to CloudWatch  
8. Failure → **SQS DLQ**

**Sam:** Yes, we need templating for both marketing and system alerts.

---

## 10:12 – Template Storage Debate
**Bob:** Should templates live in S3 or SES Template Manager?

**Alice:** SES Template Manager is simpler but limited. S3 gives version control.

**David:** S3 + KMS is better for security and flexibility.

**Sam:** Marketing wants version control.

**Alice:** Decision: **Store templates in S3, render in Lambda.**

---

## 15:40 – Scaling & Throughput
**Priya:** We need to handle bursts, possibly 500K emails/hour.

**Alice:**  
- Lambda concurrency + SQS buffering gives scale  
- SES sending rate must be raised (50/sec → 200/sec)  
- Add internal **rate-limiter** to avoid SES throttling  

**Bob:** Agreed—SES returns throttling errors if we exceed limits.

---

## 20:00 – Monitoring and Logging
**Priya:** Required monitoring additions:  
- CloudWatch metrics for success/failure counts  
- CloudWatch dashboard  
- SES failure logs → S3 (auditing)

**David:** Templates stored in S3 should be encrypted with **KMS**.

---

## 26:22 – Retry Strategy
**Bob:** Should Lambda handle retries or SQS?

**Alice:** SQS handles retries via redrive policy:

- `maxReceiveCount = 3`  
- After 3 failures → DLQ  
- Lambda logs failure reason

**Sam:** Product team needs DLQ visibility, so that works.

---

## 30:10 – API Trigger Use Case
**Sam:** Some teams want to trigger emails via API.

**Alice:** Then:  
- **API Gateway → Lambda → SNS**  
- Messages still flow through same pipeline

**Priya:** Add Cognito auth for external callers.

---

## 34:20 – Security Considerations
**David:** Security controls:  
- IAM role for Lambda limited to `ses:SendEmail`  
- S3 templates encrypted with KMS  
- VPC endpoints for S3, SNS, SQS, SES  
- Encrypt SNS + SQS with KMS  
- SES authorization policies  
- API Gateway protected by Cognito or IAM auth

---

## 38:00 – Final Architecture Summary
**Alice draws the final architecture:**

