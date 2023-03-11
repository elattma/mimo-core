"use client";

import { Button } from "@/components/ui/button";
import { useToast } from "@/lib/hooks/use-toast";

const Page = () => {
  const { toast } = useToast();

  return (
    <div>
      <button>
        {/* @ts-ignore */}
        <a href="/api/auth/login">Log in</a>
      </button>
      <Button
        onClick={() => {
          toast({ title: "Hello, world" });
        }}
      >
        Toast
      </Button>
    </div>
  );
};

export default Page;
