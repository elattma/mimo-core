"use client";

import { Dialog, DialogContent, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { TypographyLarge, TypographyMuted } from "@/components/ui/typography";
import { Plus } from "lucide-react";
import { useState } from "react";

type FakeConnection = {
  name: string;
  category: string;
};

export function ConnectionsManager() {
  const [connections, setConnections] = useState<FakeConnection[]>([]);
  const [dialogOpen, setDialogOpen] = useState<boolean>(false);

  return (
    <div className="flex flex-wrap gap-16">
      {connections.map((connection, index) => (
        <Connection connection={connection} key={`connection-${index}`} />
      ))}
      <Dialog
        open={dialogOpen}
        onOpenChange={(open) => {
          setDialogOpen(open);
        }}
      >
        <DialogTrigger asChild>
          <button className="focus-visible:default-focus group flex h-36 w-40 items-center justify-center rounded-sm border border-dashed border-neutral-7 bg-neutral-3 p-4 font-medium text-neutral-11 transition-colors hover:border-brand-7 hover:bg-brand-3 hover:text-brand-11">
            <Plus className="h-4 w-4" />
            <TypographyMuted className="transition-colors group-hover:text-brand-11">
              {connections.length === 0
                ? "Add your first connection"
                : "Add connection"}
            </TypographyMuted>
          </button>
        </DialogTrigger>
        <DialogContent className="flex flex-col pt-8">
          <Label htmlFor="new-connection-source">Source</Label>
          <Select>
            <SelectTrigger>
              <SelectValue placeholder="Select a source" />
            </SelectTrigger>
            <SelectContent>
              <SelectGroup>
                <SelectItem value="google_docs">Google Docs</SelectItem>
                <SelectItem value="google_mail">Gmail</SelectItem>
                <SelectItem value="zoho_crm">ZohoCRM</SelectItem>
                <SelectItem value="zendesk_customer_support">
                  Zendesk Support
                </SelectItem>
              </SelectGroup>
            </SelectContent>
          </Select>
          <Label htmlFor="new-connection-name">Name</Label>
          <Input id="new-connection-name" placeholder="" />
        </DialogContent>
      </Dialog>
    </div>
  );
}

type ConnectionProps = {
  connection: FakeConnection;
};

function Connection({ connection }: ConnectionProps) {
  return (
    <div className="flex flex-col rounded-sm">
      <TypographyLarge>{connection.name}</TypographyLarge>
      <TypographyMuted>{connection.category}</TypographyMuted>
    </div>
  );
}
