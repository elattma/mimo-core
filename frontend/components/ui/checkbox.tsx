import { cn } from "@/lib/util";
import * as Primitive from "@radix-ui/react-checkbox";
import { cva, VariantProps } from "class-variance-authority";
import { Check } from "lucide-react";

const checkboxVariants = cva("rounded-theme border transition-colors", {
  variants: {
    selected: {
      true: "bg-brand-bg hocus:bg-brand-bg-hover border-brand-border",
      false: "bg-transparent hocus:bg-neutral-bg-hover border-neutral-border",
    },
    size: {
      sm: "p-theme-1/8",
      default: "p-theme-1/8",
      lg: "p-theme-1/4",
    },
  },
  defaultVariants: {
    size: "default",
  },
});

const checkboxCheckVariants = cva("stroke-brand-text", {
  variants: {
    size: {
      sm: "h-2 w-2",
      default: "h-3 w-3",
      lg: "h-4 w-4",
    },
  },
  defaultVariants: {
    size: "default",
  },
});

type CheckboxProps = VariantProps<typeof checkboxVariants> &
  React.ComponentProps<typeof Primitive.Root>;

export function Checkbox({
  className,
  size,
  checked,
  ...props
}: CheckboxProps) {
  return (
    <Primitive.Root
      className={cn(
        checkboxVariants({
          selected: checked === "indeterminate" || checked,
          size,
        }),
        className
      )}
      {...props}
    >
      <div className={checkboxCheckVariants({ size })}>
        <Primitive.Indicator>
          <Check className={checkboxCheckVariants({ size })} />
        </Primitive.Indicator>
      </div>
    </Primitive.Root>
  );
}
