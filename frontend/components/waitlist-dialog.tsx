"use client";

import { Button } from "@/components/ui/button";
import { DialogClose } from "@/components/ui/dialog";
import { FormEventHandler, useState } from "react";

export default function WaitlistForm() {
  const [email, setEmail] = useState<string>("");

  const handleSubmit: FormEventHandler = (event) => {
    event.preventDefault();
    console.log(email);
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
      <DialogClose asChild>
        <Button type="submit" className="w-fit self-end">
          Join
        </Button>
      </DialogClose>
    </form>
  );
}
