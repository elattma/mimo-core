import { cn } from "@/lib/util";
import * as Primitive from "@radix-ui/react-checkbox";
import { cva } from "class-variance-authority";
import { Check } from "lucide-react";

const checkboxVariants = cva(
  "rounded-theme border p-theme-1/8 transition-colors",
  {
    variants: {
      checked: {
        true: "bg-brand-bg hocus:bg-brand-bg-hover border-brand-border",
        false: "bg-transparent hocus:bg-neutral-bg-hover border-neutral-border",
      },
    },
  }
);

type CheckboxProps = React.ComponentProps<typeof Primitive.Root>;

export function Checkbox({ className, checked, ...props }: CheckboxProps) {
  return (
    <Primitive.Root
      className={cn(
        checkboxVariants({ checked: checked === "indeterminate" || checked }),
        className
      )}
      {...props}
    >
      <div className="h-3 w-3">
        <Primitive.Indicator>
          <Check className="h-3 w-3 stroke-brand-text" />
        </Primitive.Indicator>
      </div>
    </Primitive.Root>
  );
}
