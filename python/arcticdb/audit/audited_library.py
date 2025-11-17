"""
Copyright 2023 Man Group Operations Limited

Use of this software is governed by the Business Source License 1.1 included in the file licenses/BSL.txt.

As of the Change Date specified in that file, in accordance with the Business Source License, use of this software will be governed by the Apache License, version 2.0.
"""

from typing import Any, Optional, List, Union, Tuple
from functools import wraps

from arcticdb.version_store.library import Library, WritePayload, UpdatePayload, ReadRequest, DeleteRequest
from arcticdb.version_store._store import VersionedItem
from arcticdb.version_store.processing import QueryBuilder
from arcticdb.options import OutputFormat, ArrowOutputStringFormat
from arcticdb.audit.audit_logger import AuditLogger
from arcticdb_ext.version_store import DataError


def _require_user_id(func):
    """Decorator to enforce user_id parameter."""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if 'user_id' not in kwargs or kwargs['user_id'] is None:
            raise ValueError(
                f"{func.__name__} requires 'user_id' parameter for audit logging. "
                "Please provide user_id='<your_user_id>' or user_id='<system_id>'"
            )
        return func(self, *args, **kwargs)
    return wrapper


class AuditedLibrary:
    """
    Wrapper around ArcticDB Library that enforces audit logging for all operations.
    
    This wrapper requires a user_id parameter for all read and write operations and
    automatically logs them to the audit system.
    
    Examples
    --------
    >>> import arcticdb as adb
    >>> from arcticdb.audit import AuditedLibrary, AuditLogger
    >>> 
    >>> # Create audit logger
    >>> audit_logger = AuditLogger(log_file="audit.log")
    >>> 
    >>> # Get library and wrap it
    >>> ac = adb.Arctic('lmdb://./data')
    >>> lib = ac.get_library('my_library', create_if_missing=True)
    >>> audited_lib = AuditedLibrary(lib, audit_logger)
    >>> 
    >>> # All operations now require user_id
    >>> import pandas as pd
    >>> df = pd.DataFrame({'a': [1, 2, 3]})
    >>> audited_lib.write("symbol", df, user_id="john.doe")
    >>> data = audited_lib.read("symbol", user_id="john.doe")
    """

    def __init__(self, library: Library, audit_logger: AuditLogger):
        """
        Initialize audited library wrapper.

        Parameters
        ----------
        library : Library
            The underlying ArcticDB library to wrap
        audit_logger : AuditLogger
            The audit logger instance to use for logging operations
        """
        self._library = library
        self._audit_logger = audit_logger
        self._library_name = library._nvs._lib_cfg.lib_desc.name

    def __repr__(self) -> str:
        return f"AuditedLibrary({self._library})"

    def __getattr__(self, name):
        """
        Delegate non-wrapped methods to underlying library.
        
        This allows access to methods that don't require auditing.
        """
        return getattr(self._library, name)

    @_require_user_id
    def write(
        self,
        symbol: str,
        data: Any,
        metadata: Any = None,
        prune_previous_versions: bool = False,
        staged: bool = False,
        validate_index: bool = True,
        index_column: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> VersionedItem:
        """
        Write data to a symbol with audit logging.

        Parameters
        ----------
        symbol : str
            Symbol name
        data : NormalizableType
            Data to write
        metadata : Any, default=None
            Optional metadata
        prune_previous_versions : bool, default=False
            Whether to prune previous versions
        staged : bool, default=False
            Whether to stage the write
        validate_index : bool, default=True
            Whether to validate the index
        index_column : Optional[str], default=None
            Index column for Arrow tables
        user_id : str
            Required. User ID or system ID performing the write

        Returns
        -------
        VersionedItem
            The versioned item that was written
        """
        # Log the operation
        self._audit_logger.log(
            actor=user_id,
            operation="write",
            symbols=symbol,
            library=self._library_name,
            metadata={"prune_previous_versions": prune_previous_versions, "staged": staged}
        )

        # Perform the actual write
        return self._library.write(
            symbol=symbol,
            data=data,
            metadata=metadata,
            prune_previous_versions=prune_previous_versions,
            staged=staged,
            validate_index=validate_index,
            index_column=index_column
        )

    @_require_user_id
    def read(
        self,
        symbol: str,
        as_of: Optional[Any] = None,
        date_range: Optional[Tuple[Optional[Any], Optional[Any]]] = None,
        row_range: Optional[Tuple[int, int]] = None,
        columns: Optional[List[str]] = None,
        query_builder: Optional[QueryBuilder] = None,
        lazy: bool = False,
        output_format: Optional[Union[OutputFormat, str]] = None,
        user_id: Optional[str] = None,
    ) -> Union[VersionedItem, Any]:
        """
        Read data from a symbol with audit logging.

        Parameters
        ----------
        symbol : str
            Symbol name
        as_of : Optional[Any], default=None
            Version to read
        date_range : Optional[Tuple], default=None
            Date range filter
        row_range : Optional[Tuple[int, int]], default=None
            Row range filter
        columns : Optional[List[str]], default=None
            Columns to read
        query_builder : Optional[QueryBuilder], default=None
            Query builder for filtering
        lazy : bool, default=False
            Whether to return a lazy dataframe
        output_format : Optional[Union[OutputFormat, str]], default=None
            Output format
        user_id : str
            Required. User ID or system ID performing the read

        Returns
        -------
        Union[VersionedItem, LazyDataFrame]
            The data read from the symbol
        """
        # Log the operation
        self._audit_logger.log(
            actor=user_id,
            operation="read",
            symbols=symbol,
            library=self._library_name,
            metadata={"as_of": str(as_of) if as_of else None, "lazy": lazy}
        )

        # Perform the actual read
        return self._library.read(
            symbol=symbol,
            as_of=as_of,
            date_range=date_range,
            row_range=row_range,
            columns=columns,
            query_builder=query_builder,
            lazy=lazy,
            output_format=output_format
        )

    @_require_user_id
    def write_batch(
        self,
        payloads: List[WritePayload],
        prune_previous_versions: bool = False,
        validate_index: bool = True,
        user_id: Optional[str] = None,
    ) -> List[Union[VersionedItem, DataError]]:
        """
        Write multiple symbols in batch with audit logging.

        Parameters
        ----------
        payloads : List[WritePayload]
            List of write payloads
        prune_previous_versions : bool, default=False
            Whether to prune previous versions
        validate_index : bool, default=True
            Whether to validate indices
        user_id : str
            Required. User ID or system ID performing the batch write

        Returns
        -------
        List[Union[VersionedItem, DataError]]
            Results of the batch write
        """
        symbols = [p.symbol for p in payloads]

        # Log the operation
        self._audit_logger.log(
            actor=user_id,
            operation="write_batch",
            symbols=symbols,
            library=self._library_name,
            metadata={"count": len(payloads), "prune_previous_versions": prune_previous_versions}
        )

        # Perform the actual batch write
        return self._library.write_batch(
            payloads=payloads,
            prune_previous_versions=prune_previous_versions,
            validate_index=validate_index
        )

    @_require_user_id
    def read_batch(
        self,
        symbols: List[Union[str, ReadRequest]],
        query_builder: Optional[QueryBuilder] = None,
        lazy: bool = False,
        output_format: Optional[Union[OutputFormat, str]] = None,
        user_id: Optional[str] = None,
    ) -> Union[List[Union[VersionedItem, DataError]], Any]:
        """
        Read multiple symbols in batch with audit logging.

        Parameters
        ----------
        symbols : List[Union[str, ReadRequest]]
            List of symbols or read requests
        query_builder : Optional[QueryBuilder], default=None
            Query builder to apply
        lazy : bool, default=False
            Whether to return lazy dataframes
        output_format : Optional[Union[OutputFormat, str]], default=None
            Output format
        user_id : str
            Required. User ID or system ID performing the batch read

        Returns
        -------
        Union[List[Union[VersionedItem, DataError]], LazyDataFrameCollection]
            Results of the batch read
        """
        symbol_names = [s if isinstance(s, str) else s.symbol for s in symbols]

        # Log the operation
        self._audit_logger.log(
            actor=user_id,
            operation="read_batch",
            symbols=symbol_names,
            library=self._library_name,
            metadata={"count": len(symbols), "lazy": lazy}
        )

        # Perform the actual batch read
        return self._library.read_batch(
            symbols=symbols,
            query_builder=query_builder,
            lazy=lazy,
            output_format=output_format
        )

    @_require_user_id
    def update(
        self,
        symbol: str,
        data: Any,
        metadata: Any = None,
        upsert: bool = False,
        date_range: Optional[Tuple[Optional[Any], Optional[Any]]] = None,
        prune_previous_versions: bool = False,
        user_id: Optional[str] = None,
    ) -> VersionedItem:
        """
        Update a symbol with audit logging.

        Parameters
        ----------
        symbol : str
            Symbol name
        data : NormalizableType
            Data to update
        metadata : Any, default=None
            Optional metadata
        upsert : bool, default=False
            Whether to insert if symbol doesn't exist
        date_range : Optional[Tuple], default=None
            Date range to update
        prune_previous_versions : bool, default=False
            Whether to prune previous versions
        user_id : str
            Required. User ID or system ID performing the update

        Returns
        -------
        VersionedItem
            The updated versioned item
        """
        # Log the operation
        self._audit_logger.log(
            actor=user_id,
            operation="update",
            symbols=symbol,
            library=self._library_name,
            metadata={"upsert": upsert, "prune_previous_versions": prune_previous_versions}
        )

        # Perform the actual update
        return self._library.update(
            symbol=symbol,
            data=data,
            metadata=metadata,
            upsert=upsert,
            date_range=date_range,
            prune_previous_versions=prune_previous_versions
        )

    @_require_user_id
    def append(
        self,
        symbol: str,
        data: Any,
        metadata: Any = None,
        prune_previous_versions: bool = False,
        validate_index: bool = True,
        user_id: Optional[str] = None,
    ) -> VersionedItem:
        """
        Append data to a symbol with audit logging.

        Parameters
        ----------
        symbol : str
            Symbol name
        data : NormalizableType
            Data to append
        metadata : Any, default=None
            Optional metadata
        prune_previous_versions : bool, default=False
            Whether to prune previous versions
        validate_index : bool, default=True
            Whether to validate the index
        user_id : str
            Required. User ID or system ID performing the append

        Returns
        -------
        VersionedItem
            The updated versioned item
        """
        # Log the operation
        self._audit_logger.log(
            actor=user_id,
            operation="append",
            symbols=symbol,
            library=self._library_name,
            metadata={"prune_previous_versions": prune_previous_versions}
        )

        # Perform the actual append
        return self._library.append(
            symbol=symbol,
            data=data,
            metadata=metadata,
            prune_previous_versions=prune_previous_versions,
            validate_index=validate_index
        )

    @_require_user_id
    def delete(
        self,
        symbol: str,
        versions: Optional[Any] = None,
        user_id: Optional[str] = None,
    ) -> None:
        """
        Delete a symbol or specific versions with audit logging.

        Parameters
        ----------
        symbol : str
            Symbol name
        versions : Optional[Any], default=None
            Specific versions to delete
        user_id : str
            Required. User ID or system ID performing the delete

        Returns
        -------
        None
        """
        # Log the operation
        self._audit_logger.log(
            actor=user_id,
            operation="delete",
            symbols=symbol,
            library=self._library_name,
            metadata={"versions": str(versions) if versions else "all"}
        )

        # Perform the actual delete
        return self._library.delete(symbol=symbol, versions=versions)

