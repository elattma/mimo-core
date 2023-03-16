import { cn } from "@/lib/util";
import { cva, VariantProps } from "class-variance-authority";
import { HTMLAttributes } from "react";

const loadingDotsWrapperVariants = cva("flex items-center", {
  variants: {
    size: {
      sm: "space-x-1",
      default: "space-x-1.5",
      lg: "space-x-2",
    },
  },
  defaultVariants: {
    size: "default",
  },
});

const loadingDotsVariants = cva(
  "rounded-full animate-pulse duration-[1500ms]",
  {
    variants: {
      size: {
        sm: "w-2 h-2",
        default: "w-3 h-3",
        lg: "w-4 h-4",
      },
      color: {
        brand: "bg-brand-solid",
        neutral: "bg-neutral-solid",
      },
    },
    defaultVariants: {
      size: "default",
      color: "brand",
    },
  }
);

type LoadingDotsProps = {
  size?: "sm" | "default" | "lg";
  color?: "brand" | "neutral";
} & VariantProps<typeof loadingDotsVariants> &
  HTMLAttributes<HTMLDivElement>;

function LoadingDots({ className, size, color, ...props }: LoadingDotsProps) {
  return (
    <div
      className={cn(loadingDotsWrapperVariants({ size }), className)}
      {...props}
    >
      <div className={loadingDotsVariants({ size, color })} />
      <div className={cn(loadingDotsVariants({ size, color }), "delay-100")} />
      <div className={cn(loadingDotsVariants({ size, color }), "delay-200")} />
      <div className={cn(loadingDotsVariants({ size, color }), "delay-300")} />
    </div>
  );
}

export { LoadingDots };
