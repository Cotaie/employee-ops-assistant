# Employee Ops Assistant Requirements

## 1. Purpose

Define the expected product behavior for an employee-facing assistant used by employees of an automotive company to get grounded HR and workplace-operations answers, retrieve their own employee-specific information, and initiate common requests.

## 2. Product Scope

The product shall support:

- policy and process question answering
- employee-specific questions such as leave balance, status, and benefits access
- uploaded-file summarization and discussion
- action requests such as vacation request initiation and HR ticket creation
- mixed requests that combine knowledge lookup with employee-specific checks or actions

## 3. Functional Requirements

### FR-001 Grounded Knowledge Answers

The system shall answer HR and workplace-operations questions using approved company knowledge.

Acceptance criteria:

- Given a policy or process question, the system returns an answer grounded in company knowledge.
- The answer includes source references or citations.
- If the system lacks sufficient support for an answer, it says so clearly instead of inventing guidance.

### FR-002 Employee-Specific Information Access

The system shall answer employee-specific questions using employee-scoped data.

Acceptance criteria:

- Given a question about leave balance, the system returns the current balance for the authenticated employee.
- Given a question about personal status, the system returns the employee-specific result rather than a generic policy answer.
- Given a question about benefits access, the system returns the benefits information available for the authenticated employee.

### FR-003 Action Initiation

The system shall support initiating common employee operations requests.

Acceptance criteria:

- The system supports vacation request initiation.
- The system supports HR ticket creation.
- Before any side-effect action is executed, the system asks the employee for explicit confirmation.
- After execution, the system returns the resulting status or failure reason.

### FR-004 Uploaded File Handling

The system shall support uploaded files as an additional input for summarization and discussion.

Acceptance criteria:

- Given an uploaded file, the system can summarize or discuss its contents.
- Given a smaller uploaded file, the system can analyze it directly from request context.
- Given an uploaded file larger than the configured threshold, the system routes it through ingestion and retrieval before answering.
- After the uploaded-file request is completed, the system deletes the uploaded file and any derived indexed content created only for that request.

### FR-005 Mixed Request Handling

The system shall support requests that require both policy knowledge and employee-specific handling.

Acceptance criteria:

- Given a mixed request, the system can combine policy guidance with employee-specific facts in a single response.
- Given a mixed request that includes an action, the system completes the knowledge and employee-data checks before asking for final confirmation.
- The final response clearly reflects both the knowledge-based outcome and the employee-specific or action outcome.

### FR-006 Multi-Agent Operation

The system shall use at least two distinct AI agents to support employee requests.

Acceptance criteria:

- The system includes a knowledge-focused agent.
- The system includes an operations-focused agent.
- At least one supported request path uses both agents for the same employee request.

### FR-007 Policy And Procedure Coverage

The system shall support enterprise knowledge topics relevant to employee self-service.

Acceptance criteria:

- The system can answer questions about HR policies.
- The system can answer questions about leave and benefits guidance.
- The system can answer questions about workplace or process procedures relevant to employees in the automotive company.

## 4. Non-Functional Requirements

### NFR-001 Employee Privacy

The system must protect employee-specific information.

Acceptance criteria:

- Employee-specific answers are scoped to the authenticated employee context.
- The system does not provide another employee's private information in response to a normal employee request.

### NFR-002 Answer Grounding

The system must provide traceable answers for knowledge-based responses.

Acceptance criteria:

- Knowledge-based responses expose the sources used to support the answer.
- Employee-specific responses clearly distinguish system-of-record facts from policy guidance when both appear in the same answer.

### NFR-003 Safe Actions

The system must treat external actions as confirmable operations rather than automatic side effects.

Acceptance criteria:

- The system never executes a supported external action without confirmation.
- If an action fails, the system reports the failure without claiming success.

### NFR-004 Temporary File Lifecycle

The system must treat employee-uploaded files as temporary data.

Acceptance criteria:

- Uploaded files are not retained as permanent enterprise knowledge.
- If an uploaded file was indexed for retrieval, its chunks and embeddings are deleted after the request lifecycle completes.
- Temporary uploaded-file metadata is retained only as long as needed to support the request and audit needs.
