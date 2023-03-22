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
      <section className="container flex flex-col items-center justify-center gap-theme py-theme md:flex-row">
        <div className="flex flex-col items-center gap-theme-3/4 md:w-fit md:items-start md:gap-theme lg:w-128">
          <Balancer ratio={0.75}>
            <h1 className="text-center text-5xl font-semibold leading-tight text-neutral-text-contrast md:text-start lg:text-6xl">
              Lorem ipsum dolor sit amet.
            </h1>
          </Balancer>
          <Balancer ratio={0.5}>
            <p className="text-center text-xl font-medium text-neutral-text md:text-start lg:text-2xl">
              Lorem ipsum dolor sit amet consectetur adipisicing elit. Ut sunt
              fugit cumque.
            </p>
          </Balancer>
          <Dialog>
            <DialogTrigger asChild>
              <Button className="w-fit" size="lg">
                Join Waitlist
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>
                  <h1>Join Waitlist</h1>
                </DialogTitle>
              </DialogHeader>
              <WaitlistForm />
            </DialogContent>
          </Dialog>
        </div>
        <div className="h-60 w-full shrink-0 rounded-theme bg-brand-bg md:w-96"></div>
      </section>
    </>
  );
}
