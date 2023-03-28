import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import WaitlistForm from "@/components/waitlist-dialog";
import Balancer from "react-wrap-balancer";

export default function LandingPage() {
  return (
    <>
      <section className="container flex grow flex-col items-center justify-center">
        <div className="flex max-w-2xl grow flex-col items-center justify-center pb-theme-2 xl:max-w-4xl">
          <div className="mb-theme-1/2 rounded-full border border-neutral-border bg-neutral-bg px-theme-1/2 py-theme-1/4 text-xs font-medium text-neutral-text">
            <p>Coming April 2023</p>
          </div>
          <h1 className="mb-theme-1/2 bg-gradient-to-r from-brand-9 to-brand-12 bg-clip-text text-center text-5xl font-bold text-transparent xl:text-6xl">
            <Balancer className="leading-snug">
              Any Data. From Anywhere. For Your AI Agents.
            </Balancer>
          </h1>
          <p className="mb-theme text-center text-2xl font-semibold leading-snug text-gray-text-contrast xl:text-3xl">
            <Balancer>
              Power your B2B AI SaaS with Mimo's customer data integration
              platform.
            </Balancer>
          </p>
          <Dialog>
            <DialogTrigger asChild>
              <Button className="w-fit" size="lg">
                Request Early Access
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Join Waitlist</DialogTitle>
              </DialogHeader>
              <WaitlistForm />
            </DialogContent>
          </Dialog>
        </div>
      </section>
    </>
  );
}
