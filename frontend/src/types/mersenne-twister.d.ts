declare module 'mersenne-twister' {
  export class MersenneTwister {
    constructor(seed?: number);
    random(): number;
    random_int(): number;
    random_int31(): number;
    random_incl(): number;
    random_excl(): number;
    random_long(): number;
  }
  export default MersenneTwister;
} 