import ReactMarkdown from "react-markdown";
import { FileText } from "lucide-react";

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export function PostmortemView({ markdown }: { markdown: string }) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-[var(--color-primary)]" />
          <CardTitle className="text-base">Postmortem</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        <article className="prose-sm max-w-none space-y-3 text-sm leading-relaxed [&_h2]:mt-4 [&_h2]:text-sm [&_h2]:font-semibold [&_h2]:uppercase [&_h2]:tracking-wider [&_h2]:text-[var(--color-muted-foreground)] [&_ul]:list-disc [&_ul]:pl-5 [&_p]:text-[var(--color-foreground)] [&_strong]:font-medium">
          <ReactMarkdown>{markdown}</ReactMarkdown>
        </article>
      </CardContent>
    </Card>
  );
}
