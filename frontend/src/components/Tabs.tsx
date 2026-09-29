/**
 * GOV.UK tabs, with the markup and behaviour of GOV.UK Frontend's Tabs component in React.
 *
 * GOV.UK Frontend's own script is not used: it records each tab chosen in the page's URL
 * fragment, which would add history entries and fight the router, and a page can have many
 * of these. Like it, this only works as tabs on tablet screens and wider; on smaller screens
 * the tabs are a list of links to panels shown one after another.
 */
import {
  type KeyboardEvent,
  type MouseEvent,
  type ReactNode,
  useRef,
  useState,
  useSyncExternalStore,
} from "react";

/** GOV.UK Frontend's tablet breakpoint, ``$govuk-breakpoints`` "tablet". */
const TABLET = "(min-width: 40.0625em)";

function subscribe(onChange: () => void) {
  const query = window.matchMedia?.(TABLET);
  query?.addEventListener?.("change", onChange);
  return () => query?.removeEventListener?.("change", onChange);
}

function isTabletOrWider(): boolean {
  return window.matchMedia?.(TABLET).matches ?? true;
}

export type Tab = { id: string; label: string; panel: ReactNode };

type TabsProps = {
  /** Shown above the links on small screens, where there are no tabs. */
  title: string;
  tabs: Tab[];
};

export function Tabs({ title, tabs }: TabsProps) {
  const asTabs = useSyncExternalStore(subscribe, isTabletOrWider, () => true);
  const [selected, setSelected] = useState(tabs[0]?.id ?? "");
  const links = useRef(new Map<string, HTMLAnchorElement>());

  function show(id: string, focus: boolean) {
    setSelected(id);
    if (focus) links.current.get(id)?.focus();
  }

  function onKeyDown(event: KeyboardEvent<HTMLAnchorElement>, index: number) {
    const step = { ArrowLeft: -1, Left: -1, ArrowRight: 1, Right: 1 }[event.key];
    if (step === undefined) return;
    event.preventDefault();
    const next = tabs[index + step];
    if (next) show(next.id, true);
  }

  function onClick(event: MouseEvent<HTMLAnchorElement>, id: string) {
    event.preventDefault();
    if (asTabs) show(id, false);
    else document.getElementById(id)?.scrollIntoView();
  }

  return (
    <div className="govuk-tabs">
      <h2 className="govuk-tabs__title">{title}</h2>
      <ul className="govuk-tabs__list" role={asTabs ? "tablist" : undefined}>
        {tabs.map((tab, index) => {
          const isSelected = tab.id === selected;
          return (
            <li
              key={tab.id}
              className={
                isSelected
                  ? "govuk-tabs__list-item govuk-tabs__list-item--selected"
                  : "govuk-tabs__list-item"
              }
              role={asTabs ? "presentation" : undefined}
            >
              <a
                className="govuk-tabs__tab"
                href={`#${tab.id}`}
                ref={(link) => {
                  if (link) links.current.set(tab.id, link);
                  else links.current.delete(tab.id);
                }}
                onClick={(event) => onClick(event, tab.id)}
                {...(asTabs
                  ? {
                      id: `tab_${tab.id}`,
                      role: "tab",
                      "aria-controls": tab.id,
                      "aria-selected": isSelected,
                      tabIndex: isSelected ? 0 : -1,
                      onKeyDown: (event: KeyboardEvent<HTMLAnchorElement>) =>
                        onKeyDown(event, index),
                    }
                  : {})}
              >
                {tab.label}
              </a>
            </li>
          );
        })}
      </ul>
      {tabs.map((tab) => (
        <div
          key={tab.id}
          className={
            asTabs && tab.id !== selected
              ? "govuk-tabs__panel govuk-tabs__panel--hidden"
              : "govuk-tabs__panel"
          }
          id={tab.id}
          {...(asTabs ? { role: "tabpanel", "aria-labelledby": `tab_${tab.id}` } : {})}
        >
          {tab.panel}
        </div>
      ))}
    </div>
  );
}
