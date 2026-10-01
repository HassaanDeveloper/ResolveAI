"use client";

import { cn } from "cn";
import { FileText, Search, ChevronDown, ChevronUp, Database } from "lucide-react";
import { useState } from "react";

interface PolicyEvidence {
  document_name?: string;
  name?: string;
  section?: string;
  content?: string;
  source?: string;
  version?: string;
  relevance_score?: number;
}

interface InvestigationRecord {
  type?: string;
  data?: Record<string, unknown>;
}

interface EvidenceDocument {
  document_name?: string;
  name?: string;
  source?: string;
  section?: string;
  version?: string;
  relevance_score?: number;
  content?: string;
  data?: Record<string, unknown>;
  type?: string;
}

interface EvidenceSectionProps {
  documents: EvidenceDocument[];
  status?: string;
  className?: string;
}

/**
 * The API returns policy evidence as `{ type, data: { document_name, ... } }`,
 * so the real field names live one level down inside `data`. Reading them off
 * the top-level object returned undefined and rendered "Untitled Document".
 * Both shapes are still accepted so flat items keep working.
 */
function readEvidenceField<T>(doc: EvidenceDocument, key: keyof PolicyEvidence): T | undefined {
  const nested = doc.data?.[key];
  if (nested !== undefined) return nested as T;
  return doc[key] as T | undefined;
}

export function EvidenceSection({ documents, status, className }: EvidenceSectionProps) {
  const [showRawData, setShowRawData] = useState(false);

  if (!documents || documents.length === 0) {
    if (status === "failed" || status === "rejected") {
      return (
        <div className={cn("text-center py-8", className)}>
          <Search className="h-12 w-12 mx-auto mb-4 text-muted-foreground/50" aria-hidden="true" />
          <p className="text-body text-muted-foreground">Not reached</p>
          <p className="text-body-sm text-muted-foreground mt-1">The workflow stopped before reaching the Evidence step.</p>
        </div>
      );
    }
    return (
      <div className={cn("text-center py-8", className)}>
        <Search className="h-12 w-12 mx-auto mb-4 text-muted-foreground/50" aria-hidden="true" />
        <p className="text-body text-muted-foreground">No evidence retrieved</p>
        <p className="text-body-sm text-muted-foreground mt-1">No policy documents were found relevant to this request.</p>
      </div>
    );
  }

  const policyEvidence: PolicyEvidence[] = [];
  const investigationRecords: InvestigationRecord[] = [];

  for (const doc of documents) {
    if (doc.type === "policy" || doc.document_name) {
      policyEvidence.push(doc);
    } else if (doc.type === "shipping_status" || doc.type === "order" || doc.type === "refund_calculation") {
      investigationRecords.push(doc as InvestigationRecord);
    } else if (doc.data) {
      investigationRecords.push(doc as InvestigationRecord);
    }
  }

  const hasPolicyEvidence = policyEvidence.length > 0;
  const hasInvestigationRecords = investigationRecords.length > 0;
  const hasAnyEvidence = hasPolicyEvidence || hasInvestigationRecords;

  if (!hasAnyEvidence) {
    if (status === "failed" || status === "rejected") {
      return (
        <div className={cn("text-center py-8", className)}>
          <Search className="h-12 w-12 mx-auto mb-4 text-muted-foreground/50" aria-hidden="true" />
          <p className="text-body text-muted-foreground">Not reached</p>
          <p className="text-body-sm text-muted-foreground mt-1">The workflow stopped before reaching the Evidence step.</p>
        </div>
      );
    }
    return (
      <div className={cn("text-center py-8", className)}>
        <Search className="h-12 w-12 mx-auto mb-4 text-muted-foreground/50" aria-hidden="true" />
        <p className="text-body text-muted-foreground">No evidence retrieved</p>
        <p className="text-body-sm text-muted-foreground mt-1">No policy documents were found relevant to this request.</p>
      </div>
    );
  }

  function truncateContent(content: string | undefined, maxLength: number = 200): string {
    if (!content) return "";
    if (content.length <= maxLength) return content;
    return content.slice(0, maxLength) + "...";
  }

  return (
    <div className={cn("space-y-4", className)}>
      {hasInvestigationRecords && (
        <div className="space-y-2">
          <h4 className="text-label text-muted-foreground flex items-center gap-2">
            <Database className="h-4 w-4" aria-hidden="true" />
            Investigation Findings
          </h4>
          <div className="space-y-2" role="list" aria-label="Investigation findings">
            {investigationRecords.map((record, index) => {
              const data = record.data || {};
              const recordType = record.type || "unknown";
              return (
                <div key={index} className="border border-border-default bg-surface-card rounded-lg p-3" role="listitem">
                  <p className="text-body-sm font-medium text-foreground capitalize">{recordType.replace(/_/g, " ")}</p>
                  <div className="mt-2 space-y-1">
                    {Object.entries(data).map(([key, value]) => {
                      if (typeof value === "object") return null;
                      return (
                        <div key={key} className="flex gap-2 text-body-sm">
                          <span className="text-muted-foreground capitalize min-w-[120px]">{key.replace(/_/g, " ")}:</span>
                          <span className="text-foreground">{String(value)}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {hasPolicyEvidence && (
        <div className="space-y-2">
          <h4 className="text-label text-muted-foreground">Policy Evidence ({policyEvidence.length})</h4>
          <div className="space-y-3" role="list" aria-label="Policy evidence">
            {policyEvidence.map((doc, index) => {
              const documentName =
                readEvidenceField<string>(doc, "document_name") ??
                readEvidenceField<string>(doc, "name");
              const source = readEvidenceField<string>(doc, "source");
              const section = readEvidenceField<string>(doc, "section");
              const version = readEvidenceField<string>(doc, "version");
              const content = readEvidenceField<string>(doc, "content");
              const relevanceScore = readEvidenceField<number>(doc, "relevance_score");
              return (
                <div
                  key={index}
                  className="border border-border-default bg-surface-card rounded-lg overflow-hidden"
                  role="listitem"
                >
                  <div className="p-3 border-b border-border-default bg-surface-base/50 flex items-center justify-between gap-3">
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      <FileText className="h-5 w-5 text-muted-foreground flex-shrink-0" aria-hidden="true" />
                      <div className="min-w-0">
                        <p className="text-h2 font-medium text-foreground truncate">
                          {documentName || "Untitled Document"}
                        </p>
                        <p className="text-body-sm text-muted-foreground">
                          {source && <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-muted text-muted-foreground mr-1">{source}</span>}
                          {section && <span>Section: {section}</span>}
                          {version && <span className="ml-1">v{version}</span>}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      {typeof relevanceScore === "number" && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-body-sm font-medium bg-status-complete/10 text-status-complete">
                          {Math.round(relevanceScore * 100)}%
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="p-3">
                    <p className="text-body-sm text-foreground whitespace-pre-wrap">
                      {truncateContent(content)}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {documents.length > 0 && (
        <div className="border-t border-border-default pt-2">
          <button
            type="button"
            onClick={() => setShowRawData(!showRawData)}
            className="flex items-center gap-1 text-body-sm text-muted-foreground hover:text-foreground transition-colors"
            aria-expanded={showRawData}
          >
            {showRawData ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
            {showRawData ? "Hide" : "Show"} Technical Details
          </button>
          {showRawData && (
            <div className="mt-2 border border-border-default bg-muted/30 rounded-lg p-3">
              <pre className="text-code bg-muted/50 p-2 rounded overflow-x-auto whitespace-pre-wrap font-mono text-xs leading-relaxed">
                <code>{JSON.stringify(documents.map(d => ({
                  type: d.type,
                  document_name: readEvidenceField<string>(d, "document_name"),
                  section: readEvidenceField<string>(d, "section"),
                  source: readEvidenceField<string>(d, "source"),
                  version: readEvidenceField<string>(d, "version"),
                  relevance_score: readEvidenceField<number>(d, "relevance_score"),
                  content: readEvidenceField<string>(d, "content")?.slice(0, 100) + "...",
                  data: d.data ? Object.fromEntries(Object.entries(d.data).slice(0, 5)) : undefined,
                })), null, 2)}</code>
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
