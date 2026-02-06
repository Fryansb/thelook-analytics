class SimulationError(Exception):
    """Base exception for simulation-related errors."""

    pass


class DataSourceUnavailableError(SimulationError):
    """Raised when a critical data source (Redis, PostgreSQL) is unavailable."""

    pass


class InvalidSimulationParametersError(SimulationError):
    """Raised when simulation parameters are invalid."""

    pass


class DataConsistencyError(SimulationError):
    """Raised when data consistency checks fail."""

    pass
