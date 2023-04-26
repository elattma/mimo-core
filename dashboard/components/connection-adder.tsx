"use client";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
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
import { TypographyMuted } from "@/components/ui/typography";
import useBoolean from "@/lib/hooks/use-boolean";
import { useToggle } from "@/lib/hooks/use-toggle";
import type { Integration } from "@/types";
import { Check } from "lucide-react";
import { useState } from "react";

type ConnectionAdderProps = {
  integrations: Integration[];
};

export function ConnectionAdder({ integrations }: ConnectionAdderProps) {
  const [isOpen, toggleIsOpen] = useToggle();
  const [selectedIntegration, setSelectedIntegration] =
    useState<Integration | null>(null);
  const isAuthenticated = useBoolean();
  const [name, setName] = useState<string>("");

  const handleSubmit: React.FormEventHandler = (event) => {
    event.preventDefault();
  };

  return (
    <Dialog open={isOpen} onOpenChange={toggleIsOpen}>
      <DialogTrigger asChild>
        <Button className="inline-flex">Add Connection</Button>
      </DialogTrigger>
      <DialogContent className="flex flex-col gap-4">
        <DialogTitle>New Connection</DialogTitle>
        <form className="flex flex-col gap-4" onSubmit={handleSubmit}>
          <div className="flex flex-col gap-2">
            <Label htmlFor="new-connection-source">Source</Label>
            <Select
              onValueChange={(value) => {
                const integration = integrations.find((integration) => {
                  return integration.id === value;
                });
                if (integration === undefined) {
                  return;
                }
                setSelectedIntegration(integration);
                setName(integration.name);
              }}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select a source" />
              </SelectTrigger>
              <SelectContent>
                <SelectGroup>
                  {integrations.map((integration, index) => (
                    <SelectItem
                      value={integration.id}
                      key={`integration-option-${index}`}
                    >
                      {integration.name}
                    </SelectItem>
                  ))}
                </SelectGroup>
              </SelectContent>
            </Select>
          </div>
          {selectedIntegration === null ? null : isAuthenticated.value ? (
            <div className="flex items-center space-x-2">
              <Check className="h-4 w-4 stroke-success-11" />
              <TypographyMuted className="text-success-11">
                Authenticated to {selectedIntegration.name}
              </TypographyMuted>
            </div>
          ) : (
            <Button
              type="button"
              onClick={() => isAuthenticated.setTrue()}
              fullWidth
            >
              Authenticate to {selectedIntegration.name}
            </Button>
          )}
          {isAuthenticated.value ? (
            <>
              <div className="flex flex-col gap-2">
                <Label htmlFor="new-connection-name">Name</Label>
                <Input
                  id="new-connection-name"
                  placeholder="Name your new connection"
                  value={name}
                  onChange={(event) => {
                    setName(event.target.value);
                  }}
                />
              </div>
              <Button className="self-end" type="submit">
                Add Connection
              </Button>
            </>
          ) : null}
        </form>
      </DialogContent>
    </Dialog>
  );
}
