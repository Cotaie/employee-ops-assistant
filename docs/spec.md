# Employee Ops Assistant Spec

## 1. Product Overview

Employee Ops Assistant is a multi-agent enterprise chatbot for an automotive company. It helps employees get grounded answers about HR and workplace operations, retrieve their own employee-specific information, discuss or summarize uploaded files, and initiate common requests such as vacation requests or HR support tickets.

## 2. Problem

Employees often need help with:

- HR and leave policies
- shift and workplace procedures
- personal balances, benefits, or employee-specific status
- understanding uploaded documents or files
- simple operational requests

In many companies, these questions and requests are spread across:

- policy PDFs
- internal portals
- HR teams
- managers
- ticketing systems

This creates:

- slow employee support
- repeated load on HR
- inconsistent answers
- poor self-service

## 3. Product Goal

Provide one employee-facing assistant that can:

- answer policy and process questions from company knowledge
- retrieve employee-specific data and benefits information from enterprise systems
- summarize or discuss uploaded files
- start operational actions with confirmation
- coordinate multiple AI agents behind the scenes

## 4. Users

### Primary Users

- all employees of the automotive company

## 5. Core Use Cases

### 5.1 Knowledge Questions

Examples:

- What is the overtime policy for weekend shifts?
- What documents are needed for medical leave?
- What is the internal procedure for shift swaps?
- What training is required before entering the production line?

### 5.2 Employee-Specific Questions

Examples:

- How many vacation days do I still have this year?
- Do I already have approved leave in August?
- What is my assigned shift next week?
- What benefits do I currently have access to?

### 5.3 Action Requests

Examples:

- Submit a vacation request for August 12 to August 16
- Create an HR ticket for a payroll issue
- Send a request to the appropriate support channel

### 5.4 Uploaded File Questions

Examples:

- Summarize this uploaded policy document
- Explain the main points of this uploaded PDF
- Discuss the content of this uploaded spreadsheet with me

### 5.5 Mixed Questions

Examples:

- According to policy, can I take five days off next month, and if yes, submit the request
- What is the night-shift bonus policy, and does my current shift schedule qualify for it
- Summarize this uploaded leave-related file and tell me whether it conflicts with company policy

## 6. Product Behavior

At the surface, the product behaves like a chatbot.

The product must do more than return generic text answers. It must:

- answer from company-approved knowledge
- retrieve employee-specific information when needed
- support discussion or summarization of uploaded files
- use direct file context for smaller uploaded files and indexed retrieval for larger uploaded files
- treat uploaded files as temporary data and delete them after use
- support requests that may require more than one internal capability
- ask for confirmation before side-effect actions

## 7. Internal Capability Model

The product relies on at least two distinct internal capabilities:

- one focused on policy and process knowledge
- one focused on employee-specific information and actions

These internal capabilities must be able to support the same employee request when needed.
