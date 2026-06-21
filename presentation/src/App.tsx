import {
  ArrowRight,
  ArrowRightLeft,
  Banknote,
  CheckCircle2,
  CircleDollarSign,
  ClipboardCheck,
  Database,
  FileCheck2,
  GitBranch,
  LayoutDashboard,
  LockKeyhole,
  MailCheck,
  ShieldCheck,
  Workflow,
} from "lucide-react";
import { Badge } from "./components/ui/badge";
import { Button } from "./components/ui/button";
import { Card, CardDescription, CardHeader, CardTitle } from "./components/ui/card";

const coverage = [
  {
    icon: Banknote,
    title: "Incoming funds",
    text: "Fund accounts, transaction references, duplicate protection, and confirmation posting.",
  },
  {
    icon: ClipboardCheck,
    title: "Allocations",
    text: "Project and expense-head assignment with GM and MD approval gates.",
  },
  {
    icon: FileCheck2,
    title: "Requisitions and bills",
    text: "Approved requisitions, partial billing, overbilling blocks, closure, and reversals.",
  },
  {
    icon: ArrowRightLeft,
    title: "Transfers",
    text: "Project and expense-head fund movement with pending holds until approval completes.",
  },
  {
    icon: ShieldCheck,
    title: "Audit and security",
    text: "ACLs, record rules, self-approval prevention, activities, and immutable movement history.",
  },
  {
    icon: MailCheck,
    title: "Optional parser",
    text: "A bank-email parser prototype creates pending incoming fund records for review.",
  },
];

const phases = [
  "Receive and confirm the bank transaction.",
  "Allocate money to a project and expense head.",
  "Route request to GM, then MD, with a full action trail.",
  "Spend through requisitions and bills without overspending.",
  "Move available funds between project buckets when priorities change.",
];

const evidence = [
  "Odoo 19 Community addon with Docker Compose runtime",
  "PostgreSQL-backed ledger instead of calculated-only balances",
  "Backend tests covering required and optional money-control paths",
  "Demo data and interviewer walkthrough included",
  "Recording guide included for the final facecam demo",
  "Vercel presentation site separated from the Odoo runtime",
];

const metrics = [
  { value: "24", label: "module tests" },
  { value: "0", label: "latest test failures" },
  { value: "2", label: "approval tiers" },
  { value: "6", label: "core workflows" },
];

function App() {
  return (
    <main className="min-h-screen bg-background text-foreground">
      <section className="relative isolate overflow-hidden border-b border-border bg-[#f8faf8]">
        <img
          src="/fund-management-preview.png"
          alt="Fund management dashboard preview"
          className="absolute inset-x-0 bottom-0 -z-10 h-full w-full object-cover object-center opacity-25"
        />
        <div className="absolute inset-0 -z-10 bg-white/84" />
        <div className="mx-auto flex min-h-[88svh] max-w-7xl flex-col justify-between px-5 py-5 sm:px-8 lg:px-10">
          <nav className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <span className="flex h-10 w-10 items-center justify-center rounded-md bg-primary text-primary-foreground">
                <CircleDollarSign className="h-5 w-5" aria-hidden="true" />
              </span>
              <span className="text-sm font-semibold">NNSEL Assessment</span>
            </div>
            <Button asChild variant="outline" size="sm">
              <a href="https://github.com/WhiteHades/nnsel-assesment">
                <GitBranch className="h-4 w-4" aria-hidden="true" />
                Repository
              </a>
            </Button>
          </nav>

          <div className="max-w-3xl py-16 sm:py-20 lg:py-24">
            <Badge variant="success" className="mb-5">
              Odoo 19 Community implementation
            </Badge>
            <h1 className="max-w-2xl text-5xl font-semibold leading-[1.02] text-slate-950 sm:text-6xl">
              NN Fund Management
            </h1>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-700">
              A complete fund-control module for incoming money, allocations, requisitions, bills,
              transfers, approvals, audit history, and dashboard reporting.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Button asChild size="lg">
                <a href="#coverage">
                  View scope
                  <ArrowRight className="h-4 w-4" aria-hidden="true" />
                </a>
              </Button>
              <Button asChild variant="secondary" size="lg">
                <a href="#demo">Demo path</a>
              </Button>
            </div>
          </div>

          <div className="grid gap-3 pb-4 sm:grid-cols-2 lg:grid-cols-4">
            {metrics.map((metric) => (
              <div key={metric.label} className="rounded-lg border border-white/70 bg-white/82 p-4 shadow-sm">
                <div className="text-2xl font-semibold text-slate-950">{metric.value}</div>
                <div className="mt-1 text-sm text-slate-600">{metric.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="coverage" className="border-b border-border bg-white px-5 py-16 sm:px-8 lg:px-10">
        <div className="mx-auto max-w-7xl">
          <div className="flex flex-col justify-between gap-5 md:flex-row md:items-end">
            <div>
              <Badge variant="outline">Implemented scope</Badge>
              <h2 className="mt-4 text-3xl font-semibold leading-tight text-slate-950">
                Built around money safety, approvals, and traceability.
              </h2>
            </div>
            <p className="max-w-xl text-sm leading-6 text-muted-foreground">
              The Odoo backend owns the business workflow. This presentation summarizes the module and
              points reviewers to the repository, Docker setup, tests, and demo script.
            </p>
          </div>

          <div className="mt-10 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {coverage.map((item) => (
              <Card key={item.title}>
                <CardHeader>
                  <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-md bg-slate-100 text-slate-800">
                    <item.icon className="h-5 w-5" aria-hidden="true" />
                  </div>
                  <CardTitle>{item.title}</CardTitle>
                  <CardDescription>{item.text}</CardDescription>
                </CardHeader>
              </Card>
            ))}
          </div>
        </div>
      </section>

      <section id="demo" className="border-b border-border bg-[#f5f7f4] px-5 py-16 sm:px-8 lg:px-10">
        <div className="mx-auto grid max-w-7xl gap-10 lg:grid-cols-[0.86fr_1.14fr] lg:items-start">
          <div>
            <Badge variant="warning">Interview walkthrough</Badge>
            <h2 className="mt-4 text-3xl font-semibold leading-tight text-slate-950">
              The demo follows the assessment story from receipt to spend control.
            </h2>
            <p className="mt-4 text-sm leading-6 text-muted-foreground">
              The same path is covered by backend tests, so the visible Odoo workflow and the
              verification evidence line up.
            </p>
          </div>
          <div className="grid gap-3">
            {phases.map((phase, index) => (
              <div key={phase} className="flex gap-4 rounded-lg border border-border bg-white p-4">
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-primary text-sm font-semibold text-primary-foreground">
                  {index + 1}
                </span>
                <p className="self-center text-sm font-medium leading-6 text-slate-800">{phase}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="bg-white px-5 py-16 sm:px-8 lg:px-10">
        <div className="mx-auto max-w-7xl">
          <div className="grid gap-4 lg:grid-cols-3">
            <Card>
              <CardHeader>
                <LayoutDashboard className="h-6 w-6 text-emerald-700" aria-hidden="true" />
                <CardTitle>Odoo backend UI</CardTitle>
                <CardDescription>
                  Native list, form, kanban, graph, pivot, activity, and dashboard views inside Odoo.
                </CardDescription>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader>
                <Workflow className="h-6 w-6 text-blue-700" aria-hidden="true" />
                <CardTitle>Workflow engine</CardTitle>
                <CardDescription>
                  Shared request mixin powers approval, rejection, cancellation, activities, and history.
                </CardDescription>
              </CardHeader>
            </Card>
            <Card>
              <CardHeader>
                <Database className="h-6 w-6 text-amber-700" aria-hidden="true" />
                <CardTitle>Ledger integrity</CardTitle>
                <CardDescription>
                  Every balance-impacting action writes a movement with source model and record references.
                </CardDescription>
              </CardHeader>
            </Card>
          </div>

          <div className="mt-10 grid gap-8 rounded-lg border border-border bg-slate-950 p-6 text-white lg:grid-cols-[0.78fr_1.22fr]">
            <div>
              <Badge variant="secondary">Evidence package</Badge>
              <h2 className="mt-4 text-2xl font-semibold leading-tight">Ready for local review and hosted presentation.</h2>
              <p className="mt-4 text-sm leading-6 text-slate-300">
                The repository contains the source, docs, Docker runtime, tests, and this static
                presentation site for Vercel.
              </p>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              {evidence.map((item) => (
                <div key={item} className="flex gap-3 rounded-lg border border-white/10 bg-white/5 p-4">
                  <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-emerald-300" aria-hidden="true" />
                  <span className="text-sm leading-6 text-slate-100">{item}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-8 flex flex-wrap items-center justify-between gap-4 rounded-lg border border-border bg-[#eef4f1] p-5">
            <div className="flex items-center gap-3">
              <LockKeyhole className="h-5 w-5 text-emerald-800" aria-hidden="true" />
              <p className="text-sm font-medium text-slate-900">
                Odoo and PostgreSQL run locally with Docker. Vercel hosts the public presentation only.
              </p>
            </div>
            <Button asChild variant="outline">
              <a href="https://github.com/WhiteHades/nnsel-assesment/blob/main/README.md">Read setup</a>
            </Button>
          </div>
        </div>
      </section>
    </main>
  );
}

export default App;
