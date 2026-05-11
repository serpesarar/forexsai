-- Auto-triage: classify every pending proposal into actionable buckets
-- so the user doesn't have to manually review 200+ proposals.

ALTER TABLE improvement_proposals
  ADD COLUMN IF NOT EXISTS auto_decision VARCHAR(30),
    -- 'auto_apply'   : passes all strict gates → auto-implement PR
    -- 'human_review' : ambiguous, needs eyes
    -- 'auto_reject'  : fails objective gates → close as rejected
    -- NULL           : not yet processed
  ADD COLUMN IF NOT EXISTS auto_decision_reason TEXT,
  ADD COLUMN IF NOT EXISTS auto_decided_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS auto_implemented_pr_url TEXT,
  ADD COLUMN IF NOT EXISTS auto_implementer_branch VARCHAR(255);

CREATE INDEX IF NOT EXISTS idx_improvement_proposals_auto_decision
  ON improvement_proposals (auto_decision)
  WHERE auto_decision IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_improvement_proposals_auto_pending
  ON improvement_proposals (created_at DESC)
  WHERE auto_decision IS NULL AND status = 'pending';

COMMENT ON COLUMN improvement_proposals.auto_decision IS
  'auto_apply: ready for auto-PR. human_review: ambiguous. auto_reject: fails gates. NULL: unprocessed.';
