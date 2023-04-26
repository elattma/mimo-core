"use client";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { useConnectionsContext } from "@/context/connections";
import useBoolean from "@/lib/hooks/use-boolean";
import { RefreshCcw, Trash } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

type ConnectionPageProps = {
  params: {
    id: string;
  };
};

export default function ConnectionPage({ params }: ConnectionPageProps) {
  const id = params["id"];
  const router = useRouter();
  const { connections } = useConnectionsContext();
  const connection = connections.find((connection) => connection.id === id);
  if (connection === undefined) {
    router.push("/dashboard/connections");
    return null;
  }
  const isOpen = useBoolean(false);
  const [name, setName] = useState<string>(connection.name);

  useEffect(() => isOpen.setTrue(), []);

  return (
    <Sheet
      onOpenChange={(open) => {
        if (!open) router.push("/dashboard/connections");
      }}
      open={isOpen.value}
    >
      <SheetContent className="flex flex-col gap-4" size="default">
        <SheetHeader className="mt-2">
          <SheetTitle asChild>
            <Input
              value={name}
              onChange={(event) => setName(event.target.value)}
              onBlur={() => {
                if (!name) setName(connection.name);
              }}
            />
          </SheetTitle>
        </SheetHeader>
        <div className="flex items-center justify-end gap-2">
          <Button className="flex items-center gap-2" variant="secondary">
            <RefreshCcw className="h-4 w-4" />
            <p>Resync Data</p>
          </Button>
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button className="flex items-center gap-2" variant="destructive">
                <Trash className="h-4 w-4" />
                <p>Delete</p>
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle className="text-danger-11">
                  Delete{" "}
                  <span className="font-bold text-neutral-12">
                    {connection.name}
                  </span>
                </AlertDialogTitle>
                <AlertDialogDescription>
                  This action cannot be undone. This will permanently delete
                  your connection, <b>{connection.name}</b>, and all of its
                  associated data.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction variant="destructive">
                  Delete
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>
      </SheetContent>
    </Sheet>
  );
}
