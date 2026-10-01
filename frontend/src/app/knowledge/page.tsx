"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { apiClient } from "@/lib/api";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useRefresh } from "@/lib/refresh-context";
import {
  BookOpen,
  Search,
  FileText,
  RefreshCw,
  Loader2,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Upload,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import type { DocumentsResponse, SearchResponse, KnowledgeDocument } from "@/types/api";

export default function KnowledgePage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResponse | null>(null);
  const [searchLoading, setSearchLoading] = useState(false);
  const [searchError, setSearchError] = useState(false);
  const [expandedResult, setExpandedResult] = useState<string | null>(null);
  const [ingestMsg, setIngestMsg] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();
  const { setRefreshFn } = useRefresh();

  const {
    data: docsData,
    isLoading: docsLoading,
    isRefetching: docsRefetching,
    error: docsError,
    refetch: refetchDocs,
  } = useQuery<DocumentsResponse>({
    queryKey: ["documents"],
    queryFn: async () => {
      return apiClient.getDocuments();
    },
    refetchInterval: false,
  });
  useEffect(() => { setRefreshFn(refetchDocs); return () => setRefreshFn(null); }, [refetchDocs, setRefreshFn]);

  const ingestMutation = useMutation({
    mutationFn: async (filename: string) => {
      return apiClient.ingestDocumentByName(filename);
    },
    onSuccess: () => {
      setIngestMsg({ type: "success", text: "Document ingested successfully" });
      refetchDocs();
      setTimeout(() => setIngestMsg(null), 3000);
    },
    onError: (err: any) => {
      setIngestMsg({ type: "error", text: err.detail || err.message });
    },
  });

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      return apiClient.ingestDocument(file);
    },
    onSuccess: () => {
      setIngestMsg({ type: "success", text: "Document uploaded and ingested" });
      refetchDocs();
      setTimeout(() => setIngestMsg(null), 3000);
    },
    onError: (err: any) => {
      setIngestMsg({ type: "error", text: err.detail || err.message });
    },
  });

  const searchMutation = useMutation({
    mutationFn: async (query: string) => {
      setSearchLoading(true);
      setSearchError(false);
      try {
        const result = await apiClient.searchPolicies(query);
        return result;
      } catch {
        setSearchError(true);
        return null;
      } finally {
        setSearchLoading(false);
      }
    },
    onSuccess: (data) => {
      if (data) setSearchResults(data);
    },
  });

  const docs = docsData?.data || [];

  const handleSearch = useCallback(
    (e?: React.FormEvent) => {
      e?.preventDefault();
      if (!searchQuery.trim()) return;
      searchMutation.mutate(searchQuery);
    },
    [searchQuery, searchMutation]
  );

  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    try {
      await refetchDocs();
    } finally {
      setRefreshing(false);
    }
  }, [refetchDocs]);

  const handleFileUpload = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) return;
      uploadMutation.mutate(file);
      e.target.value = "";
    },
    [uploadMutation]
  );

  const exampleQueries = [
    "refund eligibility for delayed shipment",
    "refund approval threshold",
    "cancellation after shipment",
    "escalation requirements",
  ];

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <BookOpen className="h-8 w-8" />
            Knowledge Base
          </h1>
          <p className="text-muted-foreground">
            Browse and manage company policy documents
          </p>
        </div>
        <Button variant="outline" onClick={handleRefresh} disabled={docsLoading || refreshing}>
          <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? "animate-spin" : ""}`} />
          {refreshing ? "Refreshing..." : "Refresh"}
        </Button>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Documents</CardTitle>
            <div className="flex items-center gap-2 flex-wrap">
              <div className="flex items-center gap-1">
                <FileText className="h-3 w-3 text-muted-foreground" />
                <span className="text-xs text-muted-foreground">Seed demo policies:</span>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => ingestMutation.mutate("refund_policy_v2.1.md")}
                disabled={ingestMutation.isPending}
              >
                Ingest Refund Policy
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => ingestMutation.mutate("escalation_sop_v1.0.md")}
                disabled={ingestMutation.isPending}
              >
                Ingest Escalation SOP
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => ingestMutation.mutate("cancellation_policy_v1.3.md")}
                disabled={ingestMutation.isPending}
              >
                Ingest Cancellation Policy
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => fileInputRef.current?.click()}
                disabled={uploadMutation.isPending}
              >
                <Upload className="h-3 w-3 mr-1" />
                Add Document
              </Button>
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.docx,.md,.txt"
                onChange={handleFileUpload}
                className="hidden"
              />
            </div>
          </CardHeader>
          <CardContent>
            {ingestMsg && (
              <div
                className={`mb-4 p-3 rounded-lg text-sm ${
                  ingestMsg.type === "success"
                    ? "bg-green-50 border border-green-200 text-green-700"
                    : "bg-red-50 border border-red-200 text-red-700"
                }`}
              >
                {ingestMsg.text}
              </div>
            )}

            {docsLoading ? (
              <div className="space-y-3">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Skeleton key={i} className="h-10 w-full" />
                ))}
              </div>
            ) : docsError ? (
              <div className="text-center py-8 text-red-600">
                <AlertTriangle className="h-10 w-10 mx-auto mb-2" />
                <p>Failed to load documents</p>
                <Button variant="outline" size="sm" className="mt-2" onClick={() => refetchDocs()}>
                  Retry
                </Button>
              </div>
            ) : docs.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <BookOpen className="h-12 w-12 mx-auto mb-4 text-muted-foreground/50" />
                <p>No documents found</p>
                <p className="text-sm mt-1">Click the buttons above to ingest policy documents</p>
              </div>
            ) : (
              <div className="max-h-[60vh] overflow-y-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Source</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Chunks</TableHead>
                      <TableHead>Created</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {docs.map((doc) => (
                      <TableRow key={doc.id}>
                        <TableCell className="font-medium">{doc.name}</TableCell>
                        <TableCell>{doc.source}</TableCell>
                        <TableCell>
                          <Badge variant={doc.status === "completed" ? "default" : "secondary"}>
                            {doc.status}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-sm text-muted-foreground">
                          {doc.chunk_count ?? 0}
                        </TableCell>
                        <TableCell className="text-sm text-muted-foreground">
                          {doc.created_at ? new Date(doc.created_at).toLocaleDateString() : "-"}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Search className="h-5 w-5" />
              Search Policies
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">
              Search company policies. Results come from the ingested policy documents and cite their source.
            </p>
            <form onSubmit={handleSearch} className="space-y-2">
              <Input
                placeholder="e.g., refund eligibility for delayed shipment"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="min-h-[48px]"
                disabled={searchLoading}
              />
              <Button type="submit" className="w-full" disabled={!searchQuery.trim() || searchLoading}>
                {searchLoading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Searching...
                  </>
                ) : (
                  "Search"
                )}
              </Button>
            </form>

            {searchError && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4 flex-shrink-0" />
                  <span>Search failed</span>
                </div>
                <Button variant="outline" size="sm" className="mt-2" onClick={() => handleSearch()}>
                  <RefreshCw className="h-3 w-3 mr-1" />
                  Retry
                </Button>
              </div>
            )}

            {searchResults && !searchError && (
              <div className="space-y-2">
                <p className="text-sm text-muted-foreground">
                  {searchResults.total_results} result(s) for &ldquo;{searchResults.query}&rdquo;
                </p>
                {searchResults.results.map((result, idx) => (
                  <div key={idx} className="border border-border-default rounded-lg p-3">
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-foreground">{result.document_name}</p>
                        <p className="text-xs text-muted-foreground">
                          Section: {result.section} · Score: {result.relevance_score.toFixed(4)}
                        </p>
                      </div>
                      <button
                        onClick={() => setExpandedResult(expandedResult === idx.toString() ? null : idx.toString())}
                        className="ml-2 flex-shrink-0"
                        aria-label="Toggle detail"
                      >
                        {expandedResult === idx.toString() ? (
                          <ChevronUp className="h-4 w-4" />
                        ) : (
                          <ChevronDown className="h-4 w-4" />
                        )}
                      </button>
                    </div>
                    {expandedResult === idx.toString() && (
                      <div className="mt-2 p-2 bg-muted/50 rounded text-sm text-muted-foreground">
                        {result.content.slice(0, 500)}
                        {result.content.length > 500 && "..."}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {searchResults && searchResults.results.length === 0 && !searchLoading && !searchError && (
              <div className="text-center py-6 text-muted-foreground">
                <Search className="h-8 w-8 mx-auto mb-2 text-muted-foreground/50" />
                <p className="text-sm">No relevant policy found</p>
              </div>
            )}

            <div className="p-3 bg-muted/30 rounded-lg">
              <p className="text-xs font-medium text-muted-foreground mb-2">Example queries:</p>
              <ul className="space-y-1">
                {exampleQueries.map((q) => (
                  <li key={q}>
                    <button
                      onClick={() => {
                        setSearchQuery(q);
                        handleSearch();
                      }}
                      className="text-sm text-primary hover:underline text-left w-full"
                    >
                      {q}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
