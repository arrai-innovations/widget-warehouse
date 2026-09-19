/*
    Backs the unmanaged PurchaseOrderStateCount model: one row per state of the purchase
    order workflow, with the number of orders currently in it.

    Left joined from the state table on purpose. A state holding no orders still produces a
    row, with a count of zero, which is the whole reason this exists: the workflow state
    filter on the order list rejects a state no order is in, so counting by asking the list
    endpoint once per state returns 400 exactly where a zero was wanted.

    The workflow is found through django_content_type rather than by a hardcoded id, so the
    view survives a rebuilt database where the content type ids differ.

    The join to catalog_purchaseorder is deliberate rather than decorative. An object state
    row is not part of the catalog, so truncating the catalog does not reach it, and
    reset_demo deletes those rows itself; joining the orders back means a state row that
    outlived its order cannot inflate a count here either way.

    position exists because vueda_workflow_state has no ordering column of its own and
    sorts by code, which would show the pipeline alphabetically. The codes are this
    project's own, seeded by seed_workflows, so ordering them here keeps the sequence in
    one place instead of in every consumer.
*/
DROP VIEW IF EXISTS catalog_purchaseorderstatecount;
CREATE VIEW
    catalog_purchaseorderstatecount AS
SELECT
    S.id AS id,
    S.id AS state_id,
    S.code AS code,
    S.name AS name,
    CASE S.code
        WHEN 'draft' THEN 1
        WHEN 'submitted' THEN 2
        WHEN 'approved' THEN 3
        WHEN 'received' THEN 4
        WHEN 'cancelled' THEN 5
        ELSE 99
    END AS position,
    COUNT(O.id) AS order_count
FROM
    vueda_workflow_state S
    JOIN vueda_workflow_workflow W ON W.id = S.workflow_id
    JOIN django_content_type CT ON CT.id = W.content_type_id
        AND CT.app_label = 'catalog'
        AND CT.model = 'purchaseorder'
    LEFT JOIN vueda_workflow_objectstate OS ON OS.state_id = S.id AND OS.workflow_id = W.id
    LEFT JOIN catalog_purchaseorder O ON O.id = OS.object_id
GROUP BY
    S.id,
    S.code,
    S.name
;

/*
    A view over an aggregate is not writable. These rules make a write a no-op rather than
    an error: an INSERT, UPDATE or DELETE against this relation reports success and changes
    nothing. VUEDA's own ObjectStateProxy view is set up the same way, so the behaviour
    matches the rest of the stack. The serializer is read-only for the same reason, so
    nothing in the API reaches these.
*/
CREATE OR REPLACE RULE
    catalog_purchaseorderstatecount_on_insert AS
ON INSERT TO catalog_purchaseorderstatecount DO INSTEAD NOTHING;

CREATE OR REPLACE RULE
    catalog_purchaseorderstatecount_on_update AS
ON UPDATE TO catalog_purchaseorderstatecount DO INSTEAD NOTHING;

CREATE OR REPLACE RULE
    catalog_purchaseorderstatecount_on_delete AS
ON DELETE TO catalog_purchaseorderstatecount DO INSTEAD NOTHING;
