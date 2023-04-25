import { Button } from "@/components/ui/button";

export default function LandingPage() {
  return (
    <div>
      <Button>
        {/* @ts-ignore */}
        <a href="/api/auth/login">Log in</a>
      </Button>
    </div>
  );
}
