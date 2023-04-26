import { useCallback, useState } from "react";

type UseToggleOutput = [boolean, () => void];

export function useToggle(defaultValue?: boolean): UseToggleOutput {
  const [value, setValue] = useState<boolean>(!!defaultValue);

  const toggle = useCallback(() => setValue((x) => !x), []);

  return [value, toggle];
}
