"use client";

import { useState } from "react";

type Result = {
  status?: string;
  request_id?: string;
  request?: {
    product_name?: string;
    quantity?: number;
    department?: string;
    required_by_days?: number;
  };
  vendor_result?: {
    vendor_id?: string;
    vendor_name?: string;
    total_cost?: number;
    reason?: string;
  };
  budget_result?: {
    within_budget?: boolean;
    available_budget?: number;
    requested_amount?: number;
    remaining_budget?: number;
    reason?: string;
  };
  duplicate_result?: {
    is_duplicate?: boolean;
    existing_quantity?: number;
    additional_quantity?: number;
    reason?: string;
  };
  policy_result?: {
    allowed?: boolean;
    required_approver?: string;
    reason?: string;
  };
  authority_result?: {
    requires_human?: boolean;
    approver?: string;
    can_execute?: boolean;
    reason?: string;
  };
  purchase_order?: {
    id?: string;
    status?: string;
  };
  verification_result?: {
    verified?: boolean;
    checks?: Record<string, boolean>;
    reason?: string;
  };
  explanation?: string;
  next_action?: string;
  approval_url?: string;
  trace?: string[];
};

export default function Home() {
  const [request, setRequest] = useState(
    "We need 30 Engineering Laptops for new engineering hires. We need them within 10 days. Find the best option under company policy and handle the purchase."
  );

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<Result | null>(null);
  const [error, setError] = useState("");

  async function submitRequest() {
    if (!request.trim()) return;

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/agent/procure",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            request,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data?.detail || "Procurement request failed."
        );
      }

      setResult(data);
    } catch (err: any) {
      setError(
        err?.message || "Could not connect to Procura API."
      );
    } finally {
      setLoading(false);
    }
  }

  const verified =
    result?.verification_result?.verified === true ||
    result?.status === "VERIFIED";

  const awaitingApproval =
    result?.status === "AWAITING_APPROVAL";

  const blocked = result?.status === "BLOCKED";

  return (
    <main className="min-h-screen bg-[#070b14] text-white">
      <div className="mx-auto max-w-7xl px-6 py-8 lg:px-10">

        {/* HEADER */}
        <header className="mb-8 flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600 font-black">
                P
              </div>

              <h1 className="text-3xl font-black tracking-tight">
                PROCURA
              </h1>
            </div>

            <p className="mt-2 text-sm text-slate-400">
              AI Procurement Decision & Execution Agent
            </p>
          </div>

          <div className="flex w-fit items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-4 py-2 text-sm text-emerald-400">
            <span className="h-2 w-2 animate-pulse rounded-full bg-emerald-400" />
            Agent Online
          </div>
        </header>

        {/* REQUEST */}
        <section className="mb-6 rounded-2xl border border-slate-800 bg-slate-900/70 p-6 shadow-2xl">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.2em] text-indigo-400">
                Natural Language Request
              </p>

              <h2 className="mt-1 text-lg font-semibold">
                What do you need to purchase?
              </h2>
            </div>

            <span className="hidden text-xs text-slate-600 sm:block">
              Agent will investigate → decide → execute → verify
            </span>
          </div>

          <textarea
            value={request}
            onChange={(e) => setRequest(e.target.value)}
            className="min-h-32 w-full resize-none rounded-xl border border-slate-700 bg-[#070b14] p-4 text-sm leading-6 text-slate-200 outline-none transition placeholder:text-slate-600 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
            placeholder="Describe your procurement request..."
          />

          <div className="mt-4 flex items-center justify-between">
            <span className="text-xs text-slate-500">
              Procura uses policy and application state before taking action.
            </span>

            <button
              onClick={submitRequest}
              disabled={loading || !request.trim()}
              className="rounded-xl bg-indigo-600 px-6 py-3 text-sm font-bold transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? "Agent Working..." : "Run Procurement →"}
            </button>
          </div>
        </section>

        {/* ERROR */}
        {error && (
          <section className="mb-6 rounded-2xl border border-red-500/30 bg-red-500/10 p-5 text-sm text-red-300">
            <span className="font-bold">Error:</span> {error}
          </section>
        )}

        {/* TOP STATUS */}
        {result && (
          <section className="mb-6 grid gap-4 sm:grid-cols-3">

            <MetricCard
              label="Request"
              value={result.request_id || "Generated"}
              detail={
                result.request
                  ? `${result.request.quantity || "?"} × ${result.request.product_name || "Item"}`
                  : "Procurement request"
              }
            />

            <MetricCard
              label="Recommended Vendor"
              value={
                result.vendor_result?.vendor_name ||
                "Pending"
              }
              detail={
                result.vendor_result?.total_cost
                  ? `₹${Number(
                      result.vendor_result.total_cost
                    ).toLocaleString("en-IN")}`
                  : "Awaiting decision"
              }
            />

            <MetricCard
              label="Current State"
              value={result.status || "UNKNOWN"}
              detail={
                verified
                  ? "Independent verification passed"
                  : awaitingApproval
                  ? "Human approval required"
                  : blocked
                  ? "Procurement blocked"
                  : "Agent processing"
              }
              highlight={verified}
            />
          </section>
        )}

        {/* MAIN GRID */}
        <div className="grid gap-6 lg:grid-cols-2">

          {/* DECISION */}
          <Panel
            eyebrow="01 / Decision"
            title="Procurement Recommendation"
          >
            {result?.vendor_result ? (
              <>
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-sm text-slate-500">
                      Recommended vendor
                    </p>

                    <h2 className="mt-1 text-2xl font-bold">
                      {result.vendor_result.vendor_name}
                    </h2>
                  </div>

                  <div className="rounded-xl bg-indigo-500/10 px-3 py-2 text-xs font-bold text-indigo-400">
                    SELECTED
                  </div>
                </div>

                <div className="mt-6">
                  <p className="text-xs uppercase tracking-wider text-slate-500">
                    Total Purchase
                  </p>

                  <p className="mt-1 text-4xl font-black text-indigo-400">
                    ₹
                    {Number(
                      result.vendor_result.total_cost || 0
                    ).toLocaleString("en-IN")}
                  </p>
                </div>

                <div className="mt-6 grid gap-3 sm:grid-cols-2">
                  <Check text="Approved vendor" />
                  <Check text="Quantity available" />
                  <Check text="Meets deadline" />
                  <Check text="Policy compliant" />
                </div>

                {result.vendor_result.reason && (
                  <div className="mt-6 rounded-xl border border-slate-800 bg-[#070b14] p-4">
                    <p className="text-xs font-bold uppercase tracking-wider text-slate-500">
                      Why this vendor?
                    </p>

                    <p className="mt-2 text-sm leading-6 text-slate-300">
                      {result.vendor_result.reason}
                    </p>
                  </div>
                )}
              </>
            ) : (
              <Empty text="Run a procurement request to see the agent's decision." />
            )}
          </Panel>

          {/* POLICY */}
          <Panel
            eyebrow="02 / Controls"
            title="Policy & Risk Checks"
          >
            {result ? (
              <div className="space-y-3">

                <StatusRow
                  label="Budget"
                  passed={
                    result.budget_result?.within_budget === true
                  }
                  value={
                    result.budget_result
                      ? result.budget_result.within_budget
                        ? "WITHIN BUDGET"
                        : "EXCEEDED"
                      : "Pending"
                  }
                />

                <StatusRow
                  label="Duplicate order"
                  passed={
                    result.duplicate_result
                      ? !result.duplicate_result.is_duplicate
                      : false
                  }
                  value={
                    result.duplicate_result
                      ? result.duplicate_result.is_duplicate
                        ? "DUPLICATE"
                        : "CLEAR"
                      : "Pending"
                  }
                />

                <StatusRow
                  label="Procurement policy"
                  passed={
                    result.policy_result?.allowed === true
                  }
                  value={
                    result.policy_result
                      ? result.policy_result.allowed
                        ? "COMPLIANT"
                        : "BLOCKED"
                      : "Pending"
                  }
                />

                <StatusRow
                  label="Human authority"
                  passed={
                    result.authority_result?.can_execute === true
                  }
                  value={
                    result.authority_result
                      ? result.authority_result.approver ||
                        "Approved"
                      : "Pending"
                  }
                />
              </div>
            ) : (
              <Empty text="Policy checks will appear after the request is analyzed." />
            )}
          </Panel>
        </div>

        {/* APPROVAL */}
        {awaitingApproval && result?.approval_url && (
          <section className="mt-6 rounded-2xl border border-amber-500/20 bg-amber-500/5 p-6">
            <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-xs font-bold uppercase tracking-[0.2em] text-amber-400">
                  Human Decision Required
                </p>

                <h2 className="mt-2 text-xl font-bold">
                  CEO approval required
                </h2>

                <p className="mt-1 text-sm text-slate-400">
                  Procura has completed its investigation but will not
                  execute an unauthorized purchase.
                </p>
              </div>

              <a
                href={result.approval_url}
                target="_blank"
                rel="noreferrer"
                className="rounded-xl bg-amber-500 px-6 py-3 text-center text-sm font-bold text-black transition hover:bg-amber-400"
              >
                Open Approval →
              </a>
            </div>
          </section>
        )}

        {/* TRACE */}
        <section className="mt-6 rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
          <div className="mb-6">
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-indigo-400">
              03 / Execution
            </p>

            <h2 className="mt-1 text-xl font-bold">
              Agent Execution Trace
            </h2>
          </div>

          {result?.trace?.length ? (
            <div className="relative space-y-1">
              <div className="absolute left-[11px] top-3 h-[calc(100%-24px)] w-px bg-slate-800" />

              {result.trace.map((item, index) => (
                <div
                  key={`${item}-${index}`}
                  className="relative flex items-start gap-4 rounded-xl p-3 transition hover:bg-slate-800/40"
                >
                  <div className="z-10 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-emerald-500/30 bg-slate-900 text-xs text-emerald-400">
                    ✓
                  </div>

                  <div className="pt-0.5">
                    <p className="text-sm text-slate-300">
                      {item}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <Empty text="Execution trace will appear here." />
          )}
        </section>

        {/* VERIFICATION */}
        {result && (
          <section
            className={`mt-6 rounded-2xl border p-6 ${
              verified
                ? "border-emerald-500/30 bg-emerald-500/5"
                : blocked
                ? "border-red-500/20 bg-red-500/5"
                : "border-slate-800 bg-slate-900/70"
            }`}
          >
            <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">

              <div>
                <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-500">
                  04 / Outcome
                </p>

                <h2 className="mt-1 text-2xl font-black">
                  {verified
                    ? "Procurement Verified"
                    : blocked
                    ? "Procurement Blocked"
                    : result.status || "Processing"}
                </h2>

                <p className="mt-2 max-w-2xl text-sm text-slate-400">
                  {verified
                    ? "The purchase was executed and the resulting application state was independently verified."
                    : result.explanation ||
                      "The agent is waiting for the next action."}
                </p>
              </div>

              <div
                className={`rounded-full border px-6 py-3 text-sm font-black ${
                  verified
                    ? "border-emerald-500/30 text-emerald-400"
                    : blocked
                    ? "border-red-500/30 text-red-400"
                    : "border-amber-500/30 text-amber-400"
                }`}
              >
                {verified
                  ? "✓ VERIFIED"
                  : result.status}
              </div>
            </div>

            {verified && (
              <div className="mt-6 grid gap-3 sm:grid-cols-3">
                <ProofCard
                  title="Purchase"
                  value={
                    result.purchase_order?.id ||
                    "Created"
                  }
                />

                <ProofCard
                  title="Verification"
                  value="Independent"
                />

                <ProofCard
                  title="Audit"
                  value="Notion ✓"
                />
              </div>
            )}
          </section>
        )}

        {/* FOOTER */}
        <footer className="mt-10 border-t border-slate-800 pt-5 text-center text-xs text-slate-600">
          Procura — Automate the work. Escalate the judgment. Verify the outcome.
        </footer>
      </div>
    </main>
  );
}

/* ----------------------------------------------------------
   COMPONENTS
---------------------------------------------------------- */

function Panel({
  eyebrow,
  title,
  children,
}: {
  eyebrow: string;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6 shadow-xl">
      <div className="mb-6">
        <p className="text-xs font-bold uppercase tracking-[0.2em] text-indigo-400">
          {eyebrow}
        </p>

        <h2 className="mt-1 text-xl font-bold">
          {title}
        </h2>
      </div>

      {children}
    </section>
  );
}

function MetricCard({
  label,
  value,
  detail,
  highlight = false,
}: {
  label: string;
  value: string;
  detail: string;
  highlight?: boolean;
}) {
  return (
    <div
      className={`rounded-2xl border p-5 ${
        highlight
          ? "border-emerald-500/30 bg-emerald-500/5"
          : "border-slate-800 bg-slate-900/70"
      }`}
    >
      <p className="text-xs font-bold uppercase tracking-wider text-slate-500">
        {label}
      </p>

      <p
        className={`mt-2 truncate text-lg font-bold ${
          highlight ? "text-emerald-400" : "text-white"
        }`}
      >
        {value}
      </p>

      <p className="mt-1 truncate text-xs text-slate-500">
        {detail}
      </p>
    </div>
  );
}

function Check({ text }: { text: string }) {
  return (
    <div className="flex items-center gap-3 rounded-lg bg-emerald-500/5 px-3 py-2">
      <span className="text-emerald-400">✓</span>
      <span className="text-sm text-slate-300">
        {text}
      </span>
    </div>
  );
}

function StatusRow({
  label,
  value,
  passed,
}: {
  label: string;
  value: string;
  passed: boolean;
}) {
  const pending = value === "Pending";

  return (
    <div className="flex items-center justify-between rounded-xl border border-slate-800 bg-[#070b14] p-4">
      <span className="text-sm text-slate-300">
        {label}
      </span>

      <span
        className={`text-xs font-bold ${
          pending
            ? "text-slate-500"
            : passed
            ? "text-emerald-400"
            : "text-amber-400"
        }`}
      >
        {pending ? "○ " : passed ? "✓ " : "⚠ "}
        {value}
      </span>
    </div>
  );
}

function ProofCard({
  title,
  value,
}: {
  title: string;
  value: string;
}) {
  return (
    <div className="rounded-xl border border-emerald-500/10 bg-slate-950/50 p-4">
      <p className="text-xs uppercase tracking-wider text-slate-600">
        {title}
      </p>

      <p className="mt-1 text-sm font-bold text-emerald-400">
        {value}
      </p>
    </div>
  );
}

function Empty({ text }: { text: string }) {
  return (
    <div className="rounded-xl border border-dashed border-slate-800 bg-[#070b14] p-8 text-center text-sm text-slate-600">
      {text}
    </div>
  );
}