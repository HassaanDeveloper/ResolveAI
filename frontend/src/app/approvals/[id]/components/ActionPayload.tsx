"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ClipboardList } from "lucide-react";

interface ActionPayloadProps {
  payload: Record<string, unknown>;
}

export function ActionPayload({ payload }: ActionPayloadProps) {
  return (
    <Card className="lg:col-span-1">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <ClipboardList className="h-5 w-5" />
          Action Payload
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="max-h-96 overflow-auto">
          <pre className="text-xs bg-muted p-4 rounded overflow-x-auto">
            <code>{JSON.stringify(payload, null, 2)}</code>
          </pre>
        </div>
      </CardContent>
    </Card>
  );
}