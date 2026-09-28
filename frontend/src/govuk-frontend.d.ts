// govuk-frontend ships no TypeScript declarations; declare only what we use.
declare module "govuk-frontend" {
  export class ServiceNavigation {
    constructor(root: Element);
    readonly $root: Element;
  }
}
