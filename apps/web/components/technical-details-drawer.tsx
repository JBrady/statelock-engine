"use client";

import * as Dialog from "@radix-ui/react-dialog";
import { X } from "lucide-react";
import type { ReactNode } from "react";

import { Button } from "@/components/ui/button";

type TechnicalDetailsDrawerProps = {
  title: string;
  children: ReactNode;
  triggerLabel?: string;
};

export function TechnicalDetailsDrawer({
  title,
  children,
  triggerLabel = "Technical details",
}: TechnicalDetailsDrawerProps) {
  return (
    <Dialog.Root>
      <Dialog.Trigger asChild>
        <Button variant="secondary">{triggerLabel}</Button>
      </Dialog.Trigger>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 z-40 bg-black/30 backdrop-blur-sm" />
        <Dialog.Content className="fixed inset-y-6 right-6 z-50 w-[min(760px,calc(100vw-2rem))] rounded-[2rem] border border-black/10 bg-[#fcfaf6] p-6 shadow-product focus:outline-none">
          <div className="flex items-start justify-between gap-4">
            <div>
              <Dialog.Title className="font-display text-2xl text-ink">
                {title}
              </Dialog.Title>
              <Dialog.Description className="mt-2 text-sm text-black/60">
                Raw payloads and internal field names live here, not in the primary
                UI.
              </Dialog.Description>
            </div>
            <Dialog.Close asChild>
              <button
                aria-label="Close technical details"
                className="rounded-full p-2 text-black/50 transition hover:bg-black/5"
                type="button"
              >
                <X className="h-5 w-5" />
              </button>
            </Dialog.Close>
          </div>
          <div className="mt-6 max-h-[80vh] overflow-auto rounded-[1.5rem] border border-black/10 bg-white p-4">
            {children}
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
