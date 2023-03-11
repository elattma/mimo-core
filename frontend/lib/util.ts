import { ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Creates a Tailwind class string from the given arguments
 * @param args A list of Tailwind classes, objects, and arrays
 * @returns A Tailwind class string
 */
export function cn(...args: ClassValue[]) {
  return twMerge(clsx(...args));
}

/**
 * Returns an absolute URL for a path relative to the root of the Next.js app
 * @param path A path relative to the root of the Next.js app
 * @returns An absolute URL for the given path
 */
export function absoluteUrl(path: string) {
  return `${process.env.NEXT_PUBLIC_BASE_URL}${path}`;
}

/**
 * Returns a promise that resolves after the given number of milliseconds
 * @param ms The number of milliseconds to wait
 * @returns A promise that resolves after the given number of milliseconds
 */
export function awaitTimeout(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Returns a truncated version of the given string
 * @param str String to truncate
 * @param length How many characters to keep
 * @returns A truncated version of the given string
 */
export function truncate(str: string, length: number) {
  return str.length > length ? `${str.slice(0, length)}...` : str;
}
