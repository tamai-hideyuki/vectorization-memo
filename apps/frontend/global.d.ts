// Extend global fetch mock type for Jest
import type { Mock } from 'jest';
declare global {
    var fetch: Mock;
}
