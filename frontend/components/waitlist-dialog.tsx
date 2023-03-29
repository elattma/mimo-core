"use client";

import { Button } from "@/components/ui/button";
import { DialogClose } from "@/components/ui/dialog";
import { FormEventHandler, useRef, useState } from "react";

export default function WaitlistForm() {
  const close = useRef<HTMLButtonElement>(null);
  const [email, setEmail] = useState<string>("");

  const handleSubmit: FormEventHandler = (event) => {
    event.preventDefault();
    fetch("/api/waitlist", {
      method: "POST",
      body: JSON.stringify({ message: email }),
      next: { revalidate: 1 },
    });
    close.current?.click();
  };
  return (
    <form className="flex flex-col" onSubmit={handleSubmit}>
      <label className="mb-theme-1/8 text-sm">Email</label>
      <input
        className="mb-theme rounded-theme border border-neutral-border bg-transparent p-theme-1/4 text-gray-text placeholder:text-gray-10"
        type="email"
        placeholder="name@example.com"
        value={email}
        onChange={(event) => setEmail(event.target.value)}
      />
      <Button type="submit" className="w-fit self-end">
        Join
      </Button>
      <DialogClose className="hidden" aria-hidden asChild>
        <button ref={close} />
      </DialogClose>
    </form>
  );
}
