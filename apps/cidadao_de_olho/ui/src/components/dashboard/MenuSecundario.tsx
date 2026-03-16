import * as Tabs from "@radix-ui/react-tabs";

import type { MenuSecundarioProps } from "../../types";

/** Menu secundário padrão para subtabs internas das seções. */
export function MenuSecundario({
  value,
  onValueChange,
  items,
}: MenuSecundarioProps) {
  return (
    <Tabs.Root value={value} onValueChange={onValueChange}>
      <Tabs.List className="inline-flex flex-wrap gap-2 rounded-full border border-white/8 bg-white/5 p-1">
        {items.map((item) => (
          <Tabs.Trigger
            key={item.value}
            value={item.value}
            className="rounded-full px-4 py-2 text-sm font-medium text-stone-300 outline-none transition data-[state=active]:bg-white data-[state=active]:text-[#11151f]"
          >
            {item.label}
          </Tabs.Trigger>
        ))}
      </Tabs.List>
    </Tabs.Root>
  );
}
