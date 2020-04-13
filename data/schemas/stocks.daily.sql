USE [stox]
GO

/****** Object:  Table [stocks].[daily]    Script Date: 12/04/2020 3:22:14 PM ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO

CREATE TABLE [stocks].[daily](
	[date] [date] NOT NULL,
	[market] [varchar](30) NOT NULL,
	[ticker] [varchar](30) NOT NULL,
	[open] [decimal](19, 9) NULL,
	[high] [decimal](19, 9) NULL,
	[low] [decimal](19, 9) NULL,
	[close] [decimal](19, 9) NULL,
	[volume] [decimal](19, 1) NULL,
	[dividend] [decimal](19, 9) NULL,
	[split] [decimal](19, 9) NULL,
 CONSTRAINT [PK_date-market-ticker] PRIMARY KEY CLUSTERED 
(
	[date] ASC,
	[market] ASC,
	[ticker] ASC
)WITH (	PAD_INDEX = OFF,
		STATISTICS_NORECOMPUTE = OFF,
		IGNORE_DUP_KEY = ON,
		ALLOW_ROW_LOCKS = ON,
		ALLOW_PAGE_LOCKS = ON,
		OPTIMIZE_FOR_SEQUENTIAL_KEY = ON,
		DATA_COMPRESSION = ROW
	) ON [PRIMARY]
) ON [PRIMARY]
GO

ALTER AUTHORIZATION ON [stocks].[daily] TO SCHEMA OWNER 
GO

SET ANSI_PADDING ON
GO

/****** Object:  Index [NonClusteredIndex_market-ticker]    Script Date: 12/04/2020 3:22:14 PM ******/
CREATE NONCLUSTERED INDEX [NonClusteredIndex_market-ticker] ON [stocks].[daily]
(
	[market] ASC,
	[ticker] ASC
)WITH (	PAD_INDEX = OFF,
		STATISTICS_NORECOMPUTE = OFF,
		SORT_IN_TEMPDB = OFF,
		DROP_EXISTING = OFF,
		ONLINE = OFF,
		ALLOW_ROW_LOCKS = ON,
		ALLOW_PAGE_LOCKS = ON,
		OPTIMIZE_FOR_SEQUENTIAL_KEY = ON,
		DATA_COMPRESSION = ROW
	) ON [PRIMARY]
GO

