# NovaFiber knowledge base

Twenty approved, synthetic corporate articles for a fictional US residential fiber broadband provider. All prices are USD, all policy choices are invented for this project, and no article describes a real provider or creates a legal agreement. Version 1.0 is effective and reviewed on October 7, 2026; the next planned review is January 7, 2027. This corpus is not legal advice or a claim of regulatory compliance.

## Organization and use

- `sources/customer_approved/`: 16 editable Markdown articles for the customer chatbot.
- `sources/internal_only/`: four fictional staff procedures. Do not upload these to the customer chatbot.
- `pdf/customer_approved/`: the 16 PDF files to upload through the existing administrator workspace.
- `pdf/internal_only/`: four restricted PDF examples, for a future staff-only assistant.
- `document_registry.json`: generated article metadata, PDF page counts, hashes, and related article IDs.
- `retrieval_questions.json`: expected evidence and answer criteria for retrieval evaluation. These questions are evaluation data, not policy documents; do not ingest them.

The five categories are troubleshooting (5), equipment (4), billing and plans (4), support operations (4), and general FAQs (3). The support operations documents are all internal; public troubleshooting and FAQs provide the customer-approved escalation and appointment information.

Upload only the PDFs under `pdf/customer_approved/`, one file at a time. Use PDF files for page citations. Markdown is the editable source, not a supported upload format in this MVP. The PDF ZIP is an optional download convenience; extract it before upload. Do not upload the ZIP, registry, evaluation questions, or this README.

Existing generic returns/shipping demo policies are unrelated to NovaFiber. They remain preserved but are excluded from customer retrieval once the approved NovaFiber corpus exists. Do not upload both Markdown/TXT and PDF versions of an article, since that duplicates retrieval evidence.

## Metadata and current implementation limits

`article_id` (for example NF-TS-002) is the stable business identifier. It is distinct from the UUID `document_id` assigned by the upload API and Qdrant point/chunk IDs. The registry holds title, category, topic, audience, classification, access decision, scope, owner, version, review dates, source paths, SHA-256, and page count. Header text repeats the article ID, version, and classification on each PDF page so page-level extraction keeps its provenance.

Ingestion matches known PDF hashes to registry entries and stores their article metadata with Qdrant vectors and SQLite records. Known internal PDFs are rejected. New unregistered uploads receive basic NovaFiber metadata and can be searched. Older generic demo records remain excluded. The registry is not authentication; JWT permissions are a later feature.

Citation cards open a reader that highlights the saved character range within extracted page text and links to the original PDF page. It does not annotate the PDF. A text-match check ensures the highlighted text still matches the stored excerpt.

With the local server ready, run `python scripts/ingest_knowledge_base.py`. The script uploads customer-approved PDFs; duplicate hashes prevent repeated ingestion. It uses local embeddings without calling Gemini.

The actual splitter uses 400-token windows with 60-token overlap by default; it is not the character-based splitter mentioned in the supplied reference. PDF sections pair conditions with actions and use selectable single-column text. Inspect actual chunks before changing splitter parameters.

## Policy consistency rules

Plans: Essential 100 $39/month, Everyday 300 $59/month, Home 600 $79/month, and Gig 1000 $99/month; quoted fiber speeds are up to symmetric Mbps. Month-to-month billing is in advance; no residential data cap or standard early termination charge. Standard installation is $49, one provider router/ONT is loaned without monthly rental, and conditional equipment non-return charges are $80 router / $120 ONT. Outage credit eligibility begins at a continuous verified four-hour outage and uses the formula in NF-BP-003. Rescheduling requires 24 hours' notice; missed appointments may incur $25. Relocation is $49 if service is available. Device manuals apply only to fictional NF-ONT-100 and NF-RTR-200 hardware. Specialized faults must not be inferred from the LED behavior of unrelated devices.

## Static policy versus live facts

These files contain procedures, not live outages, customer balances, ticket progress, coverage results, technician assignments, or account authorization. Those facts require authenticated operational systems in a later phase. Nova must explain its limitations and never claim to have checked an outage, opened a ticket, booked a visit, changed a plan, or applied a refund.

## Maintenance

Edit an article's Markdown source, increment its version, review related policies, then regenerate the PDFs/registry with `scripts/build_knowledge_base.py`. The exporter requires ReportLab and pypdf in its authoring environment; the chatbot's runtime dependencies are unchanged. Example: `python scripts/build_knowledge_base.py`. Do not ingest a changed policy alongside the previous version: remove the previous upload before adding the reviewed replacement until atomic version replacement is implemented. Status Approved in these artifacts represents a fictional review, not a real approval.
