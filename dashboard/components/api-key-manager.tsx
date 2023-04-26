"use client";

import { Check, Copy, Eye, EyeOff, Loader2 } from "lucide-react";
import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { TypographyMuted } from "@/components/ui/typography";
import { clientPost } from "@/lib/client-fetchers";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useToggle } from "@/lib/hooks/use-toggle";
import useBoolean from "@/lib/hooks/use-boolean";

function makeIncognito(apiKey: string): string {
  return "•".repeat(apiKey.length);
}

type ApiKeyManagerProps = {
  startingApiKey: string;
};

export function ApiKeyManager({ startingApiKey }: ApiKeyManagerProps) {
  const isDisplayingCheck = useBoolean();
  const [isDisplayingApiKey, toggleIsDisplayingApiKey] = useToggle();
  const [incognitoApiKey, setIncognitoApiKey] = useState<string>(
    makeIncognito(startingApiKey)
  );
  const [currentApiKey, setCurrentApiKey] = useState<string>(startingApiKey);
  const isLoadingNewKey = useBoolean();

  useEffect(() => {
    setIncognitoApiKey(makeIncognito(currentApiKey));
  }, [currentApiKey]);

  return (
    <div className="flex w-full flex-col items-start space-x-0 space-y-4 md:flex-row md:items-center md:space-x-4 md:space-y-0">
      <div className="flex w-full items-center justify-between overflow-hidden rounded-sm border px-2 py-1 sm:w-96">
        <TypographyMuted className="truncate whitespace-pre-wrap font-mono">
          {isDisplayingApiKey ? currentApiKey : incognitoApiKey}
        </TypographyMuted>
        <div className="flex shrink-0 items-center">
          <Tooltip delayDuration={300}>
            <TooltipTrigger asChild>
              <Button
                className="h-fit w-fit p-1.5"
                variant="ghost"
                onClick={toggleIsDisplayingApiKey}
              >
                {isDisplayingApiKey ? (
                  <>
                    <EyeOff className="h-4 w-4" />
                    <span className="sr-only">Hide API key</span>
                  </>
                ) : (
                  <>
                    <Eye className="h-4 w-4" />
                    <span className="sr-only">Show API key</span>
                  </>
                )}
              </Button>
            </TooltipTrigger>
            <TooltipContent side="bottom">
              <TypographyMuted>
                {isDisplayingApiKey ? "Hide" : "Reveal"}
              </TypographyMuted>
            </TooltipContent>
          </Tooltip>
          <Tooltip delayDuration={300}>
            <TooltipTrigger asChild>
              {isDisplayingCheck.value ? (
                <Check className="mx-1.5 h-4 w-4 stroke-green-500" />
              ) : (
                <Button
                  className="h-fit w-fit p-1.5"
                  variant="ghost"
                  onClick={() => {
                    void navigator.clipboard.writeText(currentApiKey);
                    isDisplayingCheck.setTrue();
                    setTimeout(() => {
                      isDisplayingCheck.setFalse();
                    }, 2000);
                  }}
                >
                  <Copy className="h-4 w-4" />
                  <span className="sr-only">Copy API key</span>
                </Button>
              )}
            </TooltipTrigger>
            <TooltipContent side="bottom">
              <TypographyMuted>
                {isDisplayingCheck.value ? "Copied!" : "Copy"}
              </TypographyMuted>
            </TooltipContent>
          </Tooltip>
        </div>
      </div>
      <div className="flex items-center space-x-2">
        <Button
          className="w-fit"
          variant="secondary"
          onClick={() => {
            isLoadingNewKey.setTrue();
            clientPost("/locksmith")
              .then((response) => {
                setCurrentApiKey(response.apiKey.value);
                isLoadingNewKey.setFalse();
              })
              .catch((error) => console.error(error));
          }}
          disabled={isLoadingNewKey.value}
        >
          Generate New Key
        </Button>
        {isLoadingNewKey.value ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : null}
      </div>
    </div>
  );
}
