// Minimal circuit breaker placeholder
class CircuitBreaker {
  constructor() { this.failures = 0; this.state = 'CLOSED'; }
  success() { this.failures = 0; this.state = 'CLOSED'; }
  failure() { this.failures++; if (this.failures >= 5) this.state = 'OPEN'; }
  canRequest() { return this.state !== 'OPEN'; }
}
module.exports = CircuitBreaker;
